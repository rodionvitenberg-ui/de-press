// Implementation of Depress::Client — compile only after Qt is available
// in the tdesktop build graph (linked from Telegram target).

#include "depress_client.h"

#include <QJsonArray>
#include <QJsonDocument>
#include <QNetworkCookie>
#include <QNetworkCookieJar>
#include <QUrl>
#include <QUrlQuery>

namespace Depress {
namespace {

[[nodiscard]] QVector<Story> parseStories(const QJsonDocument &doc) {
	QVector<Story> out;
	const auto root = doc.object();
	const auto items = root.value(QStringLiteral("items")).toArray();
	out.reserve(items.size());
	for (const auto &v : items) {
		const auto o = v.toObject();
		Story s;
		s.id = o.value(QStringLiteral("id")).toString();
		s.body = o.value(QStringLiteral("body")).toString();
		s.topic = o.value(QStringLiteral("topic")).toString();
		s.pseudonym = o.value(QStringLiteral("pseudonym")).toString();
		s.publishedAt = o.value(QStringLiteral("published_at")).toString();
		if (!s.id.isEmpty()) {
			out.push_back(std::move(s));
		}
	}
	return out;
}

} // namespace

Client::Client(QObject *parent)
: QObject(parent) {
}

void Client::setBaseUrl(const QString &url) {
	_baseUrl = url;
	while (_baseUrl.endsWith(QLatin1Char('/'))) {
		_baseUrl.chop(1);
	}
}

QString Client::baseUrl() const {
	return _baseUrl;
}

QNetworkRequest Client::makeRequest(const QString &path) const {
	QNetworkRequest req{ QUrl(_baseUrl + path) };
	req.setHeader(
		QNetworkRequest::ContentTypeHeader,
		QStringLiteral("application/json"));
	if (!_sessionCookie.isEmpty()) {
		req.setRawHeader(
			"Cookie",
			_sessionCookie.toUtf8());
	}
	return req;
}

void Client::setSessionCookieFromReply(QNetworkReply *reply) {
	// Prefer Set-Cookie sessionid from Django.
	const auto raw = reply->rawHeaderPairs();
	for (const auto &pair : raw) {
		if (QString::fromLatin1(pair.first).compare(
				QLatin1String("Set-Cookie"),
				Qt::CaseInsensitive) != 0) {
			continue;
		}
		const auto line = QString::fromUtf8(pair.second);
		// Keep first segment name=value
		const auto semi = line.indexOf(QLatin1Char(';'));
		const auto nv = (semi >= 0) ? line.left(semi) : line;
		if (nv.startsWith(QLatin1String("sessionid="))
			|| nv.contains(QLatin1String("sessionid="))) {
			_sessionCookie = nv.trimmed();
		}
	}
}

void Client::login(const QString &email, const QString &password) {
	QJsonObject body;
	body.insert(QStringLiteral("email"), email);
	body.insert(QStringLiteral("password"), password);
	const auto payload = QJsonDocument(body).toJson(QJsonDocument::Compact);

	auto *reply = _nam.post(
		makeRequest(QStringLiteral("/api/v1/auth/login")),
		payload);
	connect(reply, &QNetworkReply::finished, this, [this, reply] {
		reply->deleteLater();
		if (reply->error() != QNetworkReply::NoError) {
			Q_EMIT loginFinished(false, reply->errorString());
			return;
		}
		setSessionCookieFromReply(reply);
		Q_EMIT loginFinished(true, QStringLiteral("ok"));
	});
}

void Client::fetchFeed() {
	auto *reply = _nam.get(makeRequest(QStringLiteral("/api/v1/stories")));
	connect(reply, &QNetworkReply::finished, this, [this, reply] {
		reply->deleteLater();
		if (reply->error() != QNetworkReply::NoError) {
			Q_EMIT feedFinished(false, {}, reply->errorString());
			return;
		}
		const auto doc = QJsonDocument::fromJson(reply->readAll());
		if (!doc.isObject()) {
			Q_EMIT feedFinished(false, {}, QStringLiteral("bad json"));
			return;
		}
		Q_EMIT feedFinished(true, parseStories(doc), QString());
	});
}

void Client::offerEmpathy(const QString &storyId) {
	const auto path = QStringLiteral("/api/v1/stories/%1/empathy").arg(storyId);
	auto *reply = _nam.post(makeRequest(path), QByteArrayLiteral("{}"));
	connect(reply, &QNetworkReply::finished, this, [this, reply] {
		reply->deleteLater();
		if (reply->error() != QNetworkReply::NoError) {
			Q_EMIT empathyFinished(false, reply->errorString());
			return;
		}
		Q_EMIT empathyFinished(true, QStringLiteral("ok"));
	});
}

} // namespace Depress

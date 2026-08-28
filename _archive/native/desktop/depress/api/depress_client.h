// de-press HTTP client for tdesktop (Qt Network).
// Wire into Telegram after vanilla build succeeds.
//
// License note: this file is original de-press glue. When linked into
// tdesktop it becomes part of a GPLv3 combined work for the desktop binary.

#pragma once

#include <QObject>
#include <QString>
#include <QNetworkAccessManager>
#include <QNetworkReply>
#include <QVector>
#include <QJsonObject>

namespace Depress {

struct Story {
	QString id;
	QString body;
	QString topic;
	QString pseudonym;
	QString publishedAt;
};

class Client final : public QObject {
	Q_OBJECT

public:
	explicit Client(QObject *parent = nullptr);

	void setBaseUrl(const QString &url); // e.g. http://127.0.0.1:8005
	[[nodiscard]] QString baseUrl() const;

	void login(const QString &email, const QString &password);
	void fetchFeed();
	void offerEmpathy(const QString &storyId);

signals:
	void loginFinished(bool ok, const QString &message);
	void feedFinished(bool ok, const QVector<Story> &stories, const QString &message);
	void empathyFinished(bool ok, const QString &message);

private:
	void setSessionCookieFromReply(QNetworkReply *reply);
	QNetworkRequest makeRequest(const QString &path) const;

	QString _baseUrl = QStringLiteral("http://127.0.0.1:8005");
	QString _sessionCookie;
	QNetworkAccessManager _nam;
};

} // namespace Depress

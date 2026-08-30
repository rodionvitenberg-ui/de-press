import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { api } from "@/core/api/client";
import { getCachedCatalog, setCachedCatalog } from "./catalogCache";
import { translateFlatInBrowser } from "./clientTranslate";
import { applyFlat, catalogHash, flattenMessages } from "./flatten";
import {
  DEFAULT_LOCALE,
  getMessages,
  persistLocale,
  readStoredLocale,
  type Locale,
  type Messages,
} from "./index";
import { en } from "./messages/en";
import { isHandwritten } from "./uiLangs";

interface I18nContextValue {
  locale: Locale;
  messages: Messages;
  setLocale: (locale: Locale) => void;
  t: Messages;
  loading: boolean;
  catalogUnavailable: boolean;
}

const I18nContext = createContext<I18nContextValue | null>(null);

export function LocaleProvider({ children }: { children: ReactNode }) {
  const [locale, setLocaleState] = useState<Locale>(DEFAULT_LOCALE);
  const [messages, setMessages] = useState<Messages>(() => getMessages(DEFAULT_LOCALE));
  const [loading, setLoading] = useState(false);
  const [catalogUnavailable, setCatalogUnavailable] = useState(false);
  const seq = useRef(0);

  const applyLocale = useCallback(async (next: Locale) => {
    const token = ++seq.current;
    if (isHandwritten(next)) {
      if (token !== seq.current) return;
      setMessages(getMessages(next));
      setLocaleState(next);
      setCatalogUnavailable(false);
      persistLocale(next);
      return;
    }
    const flatEn = flattenMessages(en);
    const hash = catalogHash(flatEn);
    const cached = await getCachedCatalog(next, hash);
    if (cached) {
      if (token !== seq.current) return;
      const hydrated = applyFlat(en, cached);
      setMessages(hydrated);
      setLocaleState(next);
      setCatalogUnavailable(false);
      persistLocale(next);
      document.title = hydrated.meta.title;
      return;
    }
    setLoading(true);
    try {
      const pack = await api.translateUiCatalog(next, flatEn, "en");
      await setCachedCatalog(next, hash, pack.strings);
      if (token !== seq.current) return;
      const hydrated = applyFlat(en, pack.strings);
      setMessages(hydrated);
      setLocaleState(next);
      setCatalogUnavailable(false);
      persistLocale(next);
      document.title = hydrated.meta.title;
    } catch {
      /* server refused (no server translator) — try the browser's built-in
         on-device Translator API before showing the honest marker */
      const fallback = await translateFlatInBrowser(flatEn, next);
      if (token === seq.current) {
        if (fallback) {
          await setCachedCatalog(next, hash, fallback);
          const hydrated = applyFlat(en, fallback);
          setMessages(hydrated);
          setLocaleState(next);
          setCatalogUnavailable(false);
          persistLocale(next);
          document.title = hydrated.meta.title;
        } else {
          setCatalogUnavailable(true);
        }
      }
    } finally {
      if (token === seq.current) setLoading(false);
    }
  }, []);

  useEffect(() => {
    void applyLocale(readStoredLocale());
  }, [applyLocale]);

  const setLocale = useCallback(
    (next: Locale) => {
      void applyLocale(next);
    },
    [applyLocale],
  );

  const value = useMemo(
    () => ({
      locale,
      messages,
      setLocale,
      t: messages,
      loading,
      catalogUnavailable,
    }),
    [locale, messages, setLocale, loading, catalogUnavailable],
  );

  return <I18nContext.Provider value={value}>{children}</I18nContext.Provider>;
}

export function useI18n(): I18nContextValue {
  const ctx = useContext(I18nContext);
  if (!ctx) {
    throw new Error("useI18n must be used within LocaleProvider");
  }
  return ctx;
}

export function useT(): Messages {
  return useI18n().t;
}

export function useLocale(): [Locale, (locale: Locale) => void] {
  const { locale, setLocale } = useI18n();
  return [locale, setLocale];
}

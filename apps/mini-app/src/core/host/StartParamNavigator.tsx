import { useEffect, useRef } from "react";
import { useNavigate } from "react-router-dom";
import { useHost } from "./HostContext";
import {
  markStartParamApplied,
  readStartParam,
  requestEnterAntiPanic,
  resolveStartParam,
  stripStartParamFromUrl,
  wasStartParamApplied,
} from "./startParam";

/**
 * Once per Mini App (or browser ?startapp=) session: map start_param → route.
 * Renders nothing.
 */
export function StartParamNavigator() {
  const { ready } = useHost();
  const navigate = useNavigate();
  const done = useRef(false);

  useEffect(() => {
    if (!ready || done.current) return;

    const param = readStartParam();
    if (!param || wasStartParamApplied(param)) {
      done.current = true;
      return;
    }

    const target = resolveStartParam(param);
    if (!target) {
      // Unknown param: still mark applied so we don't loop
      markStartParamApplied(param);
      stripStartParamFromUrl();
      done.current = true;
      return;
    }

    markStartParamApplied(param);
    stripStartParamFromUrl();
    done.current = true;

    navigate(target.path, { replace: true });
    if (target.enterAntiPanic) {
      // After paint so Anti-Panic listeners are mounted
      window.requestAnimationFrame(() => requestEnterAntiPanic());
    }
  }, [ready, navigate]);

  return null;
}

import createMiddleware from "next-intl/middleware";
import { routing } from "./src/i18n/locales";

export default createMiddleware(routing);

export const config = {
  matcher: [
    "/",
    "/(es|en)/:path*",
    "/((?!api|_next|_vercel|.*\\..*).*)",
  ],
};

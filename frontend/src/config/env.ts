const fallbackApiBaseUrl = "http://localhost:8000";

function normalizeBaseUrl(value: string | undefined) {
  const isProduction = process.env.NODE_ENV === "production";

  if (!value) {
    if (isProduction) {
      throw new Error("NEXT_PUBLIC_API_BASE_URL is required in production");
    }
    return fallbackApiBaseUrl;
  }

  const trimmedValue = value.trim();
  const looksLikePlaceholder =
    trimmedValue.startsWith("$") ||
    (trimmedValue.startsWith("${") && trimmedValue.endsWith("}"));

  if (looksLikePlaceholder) {
    if (isProduction) {
      throw new Error("NEXT_PUBLIC_API_BASE_URL contains an unresolved placeholder");
    }
    return fallbackApiBaseUrl;
  }

  return trimmedValue.length > 0 ? trimmedValue : fallbackApiBaseUrl;
}

export const env = {
  apiBaseUrl: normalizeBaseUrl(process.env.NEXT_PUBLIC_API_BASE_URL),
};

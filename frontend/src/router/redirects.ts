export function getProtectedRedirect(isAuthenticated: boolean) {
  return isAuthenticated ? null : "/auth/login";
}

export function getPublicOnlyRedirect(isAuthenticated: boolean) {
  return isAuthenticated ? "/app" : null;
}

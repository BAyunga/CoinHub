/**
 * CoinHub Frontend Configuration
 * Dynamically switches backend URL based on environment.
 */
const CONFIG = {
  // The website and the API are served by the same Django service, so the API is always
  // reached through the relative path '/api' (locally via Nginx, in production via WhiteNoise/Django).
  API_BASE: '/api',
    
  POLL_INTERVAL_MS: 3000,
  POLL_MAX_ATTEMPTS: 20,
  // Fallbacks only. The real minimum and step come from the API for each coin (set in the database).
  COIN_MIN: 1000,
  COIN_STEP: 1000,
};

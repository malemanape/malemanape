/**
 * The profile banner, with the sky for the time of day where El lives, picked the moment
 * someone opens the profile. GitHub only runs the scheduled Action when it has room, so a
 * banner drawn by the Action can show the morning sun at midnight; this can't.
 *
 * GET /api/banner?theme=light|dark
 * The Action draws every sky ahead of time (scripts/art.py writes assets/banner-<when>-<theme>.svg),
 * so this only picks one. The times of day and the timezone come from profile.config.json.
 * Cached for five minutes, so a new sky shows within a few minutes of the hour it starts.
 */
const fs = require('fs');
const path = require('path');
const cfg = require('../profile.config.json');

/** Which part of the day it is now, in the config's timezone: the last one that has started. */
function now() {
  const hour = Number(new Intl.DateTimeFormat('en-GB', { timeZone: cfg.timezone, hour: '2-digit', hourCycle: 'h23' }).format(new Date()));
  const started = cfg.day.filter((p) => hour >= p.from);
  return (started.length ? started[started.length - 1] : cfg.day[cfg.day.length - 1]).name; // before the first, it's still night
}

module.exports = (req, res) => {
  const theme = req.query.theme === 'dark' ? 'dark' : 'light';
  const file = path.join(process.cwd(), 'assets', `banner-${now()}-${theme}.svg`);
  res.setHeader('Content-Type', 'image/svg+xml; charset=utf-8');
  res.setHeader('Cache-Control', 'public, max-age=300, s-maxage=300');
  res.end(fs.readFileSync(file));
};

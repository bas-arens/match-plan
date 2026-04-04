let timers = {};

export function autosave(key, callback, delay = 600) {
  clearTimeout(timers[key]);
  timers[key] = setTimeout(() => {
    callback();
  }, delay);
}

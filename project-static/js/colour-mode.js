function getPreferredColourMode() {
  const storedMode = localStorage.getItem('peeringmanager-colour-mode');
  const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;

  if (storedMode) {
    return storedMode;
  }

  return prefersDark ? 'dark' : 'light';
}

function getCurrentColourMode() {
  return document.documentElement.getAttribute('data-bs-theme') || 'light';
}

function setColourMode(mode, button, button_only = false) {
  if (!button_only) {
    document.documentElement.setAttribute('data-bs-theme', mode);
    localStorage.setItem('peeringmanager-colour-mode', mode);
  }

  if (mode === 'dark') {
    button.innerHTML = '<i class="fa-fw fa-solid fa-moon"></i>';
  } else {
    button.innerHTML = '<i class="fa-fw fa-solid fa-sun"></i>';
  }
}

document.documentElement.setAttribute('data-bs-theme', getPreferredColourMode());

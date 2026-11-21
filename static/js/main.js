// Wellness Program Management System - Main Script
document.addEventListener('DOMContentLoaded', function () {
  // Auto-dismiss alerts after 5 seconds
  const alerts = document.querySelectorAll('.alert-dismissible');
  alerts.forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      if (bsAlert) {
        bsAlert.close();
      }
    }, 5000);
  });

  // Demo Login quick fill helper
  const demoButtons = document.querySelectorAll('.demo-login-btn');
  demoButtons.forEach(function (btn) {
    btn.addEventListener('click', function () {
      const username = this.getAttribute('data-user');
      const password = this.getAttribute('data-pass') || 'Demo@1234';
      const userInput = document.querySelector('input[name="username"]');
      const passInput = document.querySelector('input[name="password"]');
      if (userInput && passInput) {
        userInput.value = username;
        passInput.value = password;
        // submit the form automatically for seamless 1-click test
        const form = userInput.closest('form');
        if (form) {
          form.submit();
        }
      }
    });
  });
});

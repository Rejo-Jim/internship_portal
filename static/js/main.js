document.addEventListener("DOMContentLoaded", function () {
  // Auto-dismiss alerts after 4 seconds
  document.querySelectorAll(".alert.auto-dismiss").forEach(function (alert) {
    setTimeout(function () {
      const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
      bsAlert.close();
    }, 4000);
  });

  // Sidebar toggle on mobile
  const toggleBtn = document.getElementById("sidebarToggle");
  const sidebar = document.querySelector(".sidebar");
  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener("click", function () {
      sidebar.classList.toggle("show");
    });
  }

  // Password visibility toggle
  document.querySelectorAll(".toggle-password").forEach(function (btn) {
    btn.addEventListener("click", function () {
      const targetId = btn.getAttribute("data-target");
      const input = document.getElementById(targetId);
      if (!input) return;
      if (input.type === "password") {
        input.type = "text";
        btn.innerHTML = '<i class="bi bi-eye-slash"></i>';
      } else {
        input.type = "password";
        btn.innerHTML = '<i class="bi bi-eye"></i>';
      }
    });
  });

  // Confirmation dialogs for destructive actions
  document.querySelectorAll("form[data-confirm]").forEach(function (form) {
    form.addEventListener("submit", function (e) {
      const message = form.getAttribute("data-confirm") || "Are you sure?";
      if (!confirm(message)) {
        e.preventDefault();
      }
    });
  });

  // Live search/filter (client-side) for tables with data-filter-table
  document.querySelectorAll("[data-live-search]").forEach(function (input) {
    input.addEventListener("keyup", function () {
      const tableSelector = input.getAttribute("data-live-search");
      const table = document.querySelector(tableSelector);
      if (!table) return;
      const filter = input.value.toLowerCase();
      table.querySelectorAll("tbody tr").forEach(function (row) {
        row.style.display = row.textContent.toLowerCase().includes(filter) ? "" : "none";
      });
    });
  });

  // Interview countdown badges
  document.querySelectorAll("[data-interview-date]").forEach(function (el) {
    const dateStr = el.getAttribute("data-interview-date");
    if (!dateStr) return;
    const target = new Date(dateStr + "T00:00:00");
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    const diffDays = Math.round((target - today) / (1000 * 60 * 60 * 24));
    if (diffDays === 0) {
      el.textContent = "Today";
      el.classList.add("deadline-soon");
    } else if (diffDays === 1) {
      el.textContent = "Tomorrow";
      el.classList.add("deadline-soon");
    } else if (diffDays > 1 && diffDays <= 7) {
      el.textContent = "In " + diffDays + " days";
      el.classList.add("deadline-soon");
    } else if (diffDays < 0) {
      el.textContent = "Past";
    } else {
      el.textContent = "In " + diffDays + " days";
    }
  });

  // Simple client-side required-field validation feedback (backend always validates too)
  document.querySelectorAll("form.needs-validation").forEach(function (form) {
    form.addEventListener(
      "submit",
      function (event) {
        if (!form.checkValidity()) {
          event.preventDefault();
          event.stopPropagation();
        }
        form.classList.add("was-validated");
      },
      false
    );
  });
});

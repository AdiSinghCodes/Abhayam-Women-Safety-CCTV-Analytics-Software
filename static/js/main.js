// Main JavaScript for Abhayam Women Safety Analytics

document.addEventListener("DOMContentLoaded", () => {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
    var tooltipList = tooltipTriggerList.map((tooltipTriggerEl) => new bootstrap.Tooltip(tooltipTriggerEl))
  
    // Add fade-in animation to cards
    const cards = document.querySelectorAll(".card")
    cards.forEach((card) => {
      card.classList.add("fade-in")
    })
  
    // Close alert messages after 5 seconds
    const alerts = document.querySelectorAll(".alert")
    alerts.forEach((alert) => {
      setTimeout(() => {
        const bsAlert = new bootstrap.Alert(alert)
        bsAlert.close()
      }, 5000)
    })
  
    // Add active class to current nav item
    const currentLocation = window.location.pathname
    const navLinks = document.querySelectorAll(".nav-link")
    navLinks.forEach((link) => {
      if (link.getAttribute("href") === currentLocation) {
        link.classList.add("active")
      }
    })
  })
  
  // Function to show loading spinner
  function showLoading(elementId, message = "Loading...") {
    const element = document.getElementById(elementId)
    if (element) {
      element.innerHTML = `
              <div class="d-flex align-items-center">
                  <div class="spinner-border spinner-border-sm text-primary me-2" role="status">
                      <span class="visually-hidden">Loading...</span>
                  </div>
                  <span>${message}</span>
              </div>
          `
    }
  }
  
  // Function to hide loading spinner
  function hideLoading(elementId) {
    const element = document.getElementById(elementId)
    if (element) {
      element.innerHTML = ""
    }
  }
  
  // Function to show notification
  function showNotification(message, type = "success") {
    const notificationArea = document.createElement("div")
    notificationArea.className = `toast align-items-center text-white bg-${type} border-0 position-fixed top-0 end-0 m-3`
    notificationArea.setAttribute("role", "alert")
    notificationArea.setAttribute("aria-live", "assertive")
    notificationArea.setAttribute("aria-atomic", "true")
  
    notificationArea.innerHTML = `
          <div class="d-flex">
              <div class="toast-body">
                  ${message}
              </div>
              <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
          </div>
      `
  
    document.body.appendChild(notificationArea)
    const toast = new bootstrap.Toast(notificationArea)
    toast.show()
  
    // Remove from DOM after hiding
    notificationArea.addEventListener("hidden.bs.toast", () => {
      document.body.removeChild(notificationArea)
    })
  }
  
  
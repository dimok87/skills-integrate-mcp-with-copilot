document.addEventListener("DOMContentLoaded", () => {
  const activitiesList = document.getElementById("activities-list");
  const activitySelect = document.getElementById("activity");
  const signupForm = document.getElementById("signup-form");
  const messageDiv = document.getElementById("message");
  const authStatus = document.getElementById("auth-status");
  const authMessageDiv = document.getElementById("auth-message");
  const loginForm = document.getElementById("login-form");
  const registerForm = document.getElementById("register-form");
  const logoutBtn = document.getElementById("logout-btn");
  const signupEmailInput = document.getElementById("email");

  let authToken = localStorage.getItem("authToken");
  let currentUser = null;

  function showMessage(target, text, type = "info") {
    target.textContent = text;
    target.className = type;
    target.classList.remove("hidden");

    setTimeout(() => {
      target.classList.add("hidden");
    }, 5000);
  }

  function getAuthHeaders() {
    if (!authToken) {
      return {};
    }
    return { Authorization: `Bearer ${authToken}` };
  }

  function updateAuthUi() {
    if (currentUser) {
      authStatus.textContent = `Logged in as ${currentUser.email} (${currentUser.role})`;
      logoutBtn.classList.remove("hidden");
      loginForm.classList.add("hidden");
      registerForm.classList.add("hidden");

      signupEmailInput.value = currentUser.email;
      signupEmailInput.readOnly = currentUser.role !== "admin";
      signupEmailInput.required = currentUser.role === "admin";
    } else {
      authStatus.textContent = "Not logged in";
      logoutBtn.classList.add("hidden");
      loginForm.classList.remove("hidden");
      registerForm.classList.remove("hidden");

      signupEmailInput.value = "";
      signupEmailInput.readOnly = false;
      signupEmailInput.required = false;
    }
  }

  async function loadSession() {
    if (!authToken) {
      currentUser = null;
      updateAuthUi();
      return;
    }

    try {
      const response = await fetch("/auth/session", {
        headers: getAuthHeaders(),
      });

      if (!response.ok) {
        throw new Error("Session expired");
      }

      const result = await response.json();
      currentUser = result.user;
    } catch (error) {
      authToken = null;
      currentUser = null;
      localStorage.removeItem("authToken");
    }

    updateAuthUi();
  }

  // Function to fetch activities from API
  async function fetchActivities() {
    try {
      const response = await fetch("/activities");
      const activities = await response.json();

      // Clear loading message
      activitiesList.innerHTML = "";
      activitySelect.innerHTML = '<option value="">-- Select an activity --</option>';

      // Populate activities list
      Object.entries(activities).forEach(([name, details]) => {
        const activityCard = document.createElement("div");
        activityCard.className = "activity-card";

        const spotsLeft =
          details.max_participants - details.participants.length;

        // Create participants HTML with delete icons instead of bullet points
        const participantsHTML =
          details.participants.length > 0
            ? `<div class="participants-section">
              <h5>Participants:</h5>
              <ul class="participants-list">
                ${details.participants
                  .map(
                    (email) => {
                      const canDelete =
                        currentUser &&
                        (currentUser.role === "admin" || currentUser.email === email);
                      const deleteButton = canDelete
                        ? `<button class="delete-btn" data-activity="${name}" data-email="${email}">❌</button>`
                        : "";
                      return `<li><span class="participant-email">${email}</span>${deleteButton}</li>`;
                    }
                  )
                  .join("")}
              </ul>
            </div>`
            : `<p><em>No participants yet</em></p>`;

        activityCard.innerHTML = `
          <h4>${name}</h4>
          <p>${details.description}</p>
          <p><strong>Schedule:</strong> ${details.schedule}</p>
          <p><strong>Availability:</strong> ${spotsLeft} spots left</p>
          <div class="participants-container">
            ${participantsHTML}
          </div>
        `;

        activitiesList.appendChild(activityCard);

        // Add option to select dropdown
        const option = document.createElement("option");
        option.value = name;
        option.textContent = name;
        activitySelect.appendChild(option);
      });

      // Add event listeners to delete buttons
      document.querySelectorAll(".delete-btn").forEach((button) => {
        button.addEventListener("click", handleUnregister);
      });
    } catch (error) {
      activitiesList.innerHTML =
        "<p>Failed to load activities. Please try again later.</p>";
      console.error("Error fetching activities:", error);
    }
  }

  // Handle unregister functionality
  async function handleUnregister(event) {
    if (!currentUser) {
      showMessage(messageDiv, "Please log in to unregister.", "error");
      return;
    }

    const button = event.target;
    const activity = button.getAttribute("data-activity");
    const email = button.getAttribute("data-email");

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(
          activity
        )}/unregister?email=${encodeURIComponent(email)}`,
        {
          method: "DELETE",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(messageDiv, result.message, "success");

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to unregister. Please try again.", "error");
      console.error("Error unregistering:", error);
    }
  }

  registerForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.getElementById("register-email").value,
      password: document.getElementById("register-password").value,
      role: document.getElementById("register-role").value,
    };

    try {
      const response = await fetch("/auth/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        showMessage(authMessageDiv, result.detail || "Registration failed.", "error");
        return;
      }

      showMessage(authMessageDiv, "Registration successful. You can now log in.", "success");
      registerForm.reset();
    } catch (error) {
      showMessage(authMessageDiv, "Registration failed. Please try again.", "error");
      console.error("Error registering:", error);
    }
  });

  loginForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    const payload = {
      email: document.getElementById("login-email").value,
      password: document.getElementById("login-password").value,
    };

    try {
      const response = await fetch("/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const result = await response.json();

      if (!response.ok) {
        showMessage(authMessageDiv, result.detail || "Login failed.", "error");
        return;
      }

      authToken = result.token;
      currentUser = result.user;
      localStorage.setItem("authToken", authToken);
      updateAuthUi();
      showMessage(authMessageDiv, "Logged in successfully.", "success");
      loginForm.reset();
      fetchActivities();
    } catch (error) {
      showMessage(authMessageDiv, "Login failed. Please try again.", "error");
      console.error("Error logging in:", error);
    }
  });

  logoutBtn.addEventListener("click", async () => {
    try {
      await fetch("/auth/logout", {
        method: "POST",
        headers: getAuthHeaders(),
      });
    } catch (error) {
      console.error("Error logging out:", error);
    }

    authToken = null;
    currentUser = null;
    localStorage.removeItem("authToken");
    updateAuthUi();
    fetchActivities();
    showMessage(authMessageDiv, "Logged out.", "info");
  });

  // Handle form submission
  signupForm.addEventListener("submit", async (event) => {
    event.preventDefault();

    if (!currentUser) {
      showMessage(messageDiv, "Please log in before signing up.", "error");
      return;
    }

    const email = signupEmailInput.value.trim();
    const activity = document.getElementById("activity").value;

    const queryEmail = currentUser.role === "admin" && email ? `?email=${encodeURIComponent(email)}` : "";

    try {
      const response = await fetch(
        `/activities/${encodeURIComponent(activity)}/signup${queryEmail}`,
        {
          method: "POST",
          headers: getAuthHeaders(),
        }
      );

      const result = await response.json();

      if (response.ok) {
        showMessage(messageDiv, result.message, "success");
        signupForm.reset();

        if (currentUser) {
          signupEmailInput.value = currentUser.email;
        }

        // Refresh activities list to show updated participants
        fetchActivities();
      } else {
        showMessage(messageDiv, result.detail || "An error occurred", "error");
      }
    } catch (error) {
      showMessage(messageDiv, "Failed to sign up. Please try again.", "error");
      console.error("Error signing up:", error);
    }
  });

  // Initialize app
  loadSession().then(fetchActivities);
});

/**
 * Student Complaint & Solution Tracker (SCST)
 * Student Experience Client Scripts
 */

document.addEventListener('DOMContentLoaded', () => {
  initComplaintFormValidation();
});

function initComplaintFormValidation() {
  const form = document.querySelector('#complaintForm');
  if (!form) return;

  const categorySelect = form.querySelector('#category');
  const descriptionText = form.querySelector('#description');
  const locationInput = form.querySelector('#location');

  form.addEventListener('submit', (e) => {
    let isValid = true;

    // Category check
    if (!categorySelect.value || categorySelect.value === 'Select Category') {
      showFieldError(categorySelect, 'Please select a complaint category.');
      isValid = false;
    } else {
      clearFieldError(categorySelect);
    }

    // Description check
    if (!descriptionText.value.trim()) {
      showFieldError(descriptionText, 'Please provide a description of the issue.');
      isValid = false;
    } else if (descriptionText.value.trim().length < 10) {
      showFieldError(descriptionText, 'Please provide at least 10 characters describing the issue.');
      isValid = false;
    } else {
      clearFieldError(descriptionText);
    }

    // Location check
    if (!locationInput.value.trim()) {
      showFieldError(locationInput, 'Please specify the exact location on campus.');
      isValid = false;
    } else {
      clearFieldError(locationInput);
    }

    if (!isValid) {
      e.preventDefault();
      if (window.showToast) {
        window.showToast('error', 'Form Incomplete', 'Please fill in all required fields marked with *');
      }
    }
  });

  // Clear errors on input
  [categorySelect, descriptionText, locationInput].forEach((el) => {
    if (el) {
      el.addEventListener('input', () => clearFieldError(el));
      el.addEventListener('change', () => clearFieldError(el));
    }
  });
}

function showFieldError(inputElement, errorMessage) {
  const group = inputElement.closest('.form-group');
  if (!group) return;

  group.classList.add('has-error');
  let feedback = group.querySelector('.form-error-feedback');
  if (!feedback) {
    feedback = document.createElement('div');
    feedback.className = 'form-error-feedback';
    group.appendChild(feedback);
  }
  feedback.textContent = errorMessage;
}

function clearFieldError(inputElement) {
  const group = inputElement.closest('.form-group');
  if (!group) return;
  group.classList.remove('has-error');
}

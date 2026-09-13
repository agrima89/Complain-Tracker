/**
 * Student Complaint & Solution Tracker (SCST)
 * Student Experience Client Scripts & Micro-Interactions
 */

document.addEventListener('DOMContentLoaded', () => {
  initComplaintPhotoUploader();
  initLocationParamAutoSelect();
  initComplaintFormValidation();
  initPriorityChipSelector();
  initDescriptionCharCounter();
  initProgressIndicatorTracker();
});

/**
 * Helper to format file sizes nicely
 */
function formatFileSize(bytes) {
  if (bytes === 0) return '0 Bytes';
  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));
  return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
}

/**
 * Interactive Photo Uploader with Live Preview and File State Management
 */
function initComplaintPhotoUploader() {
  const container = document.getElementById('photoUploadContainer');
  const fileInput = document.getElementById('photoInput');
  const promptState = document.getElementById('photoPromptState');
  const previewState = document.getElementById('photoPreviewState');
  const previewImg = document.getElementById('imagePreviewElement');
  const filenameLabel = document.getElementById('photoFilenameLabel');
  const browseBtn = document.getElementById('browsePhotoBtn');
  const changeBtn = document.getElementById('changePhotoBtn');
  const removeBtn = document.getElementById('removePhotoBtn');
  const errorText = document.getElementById('photoErrorText');

  if (!container || !fileInput) return;

  // Clicking container opens file picker when in prompt state
  container.addEventListener('click', (e) => {
    if (e.target.closest('#changePhotoBtn') || e.target.closest('#removePhotoBtn')) return;
    if (previewState.style.display !== 'flex') {
      fileInput.click();
    }
  });

  // Browse button trigger
  if (browseBtn) {
    browseBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  // Change button trigger
  if (changeBtn) {
    changeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.click();
    });
  }

  // Remove photo
  if (removeBtn) {
    removeBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      fileInput.value = '';
      previewImg.src = '';
      previewState.style.display = 'none';
      promptState.style.display = 'block';
      if (errorText) errorText.style.display = 'none';
      container.style.borderColor = 'rgba(56, 189, 248, 0.32)';
      container.classList.remove('has-image');
      updateStepProgress();
    });
  }

  // File input change handler
  fileInput.addEventListener('change', (e) => {
    const file = fileInput.files[0];
    if (file) {
      // Validate image type
      const validTypes = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
      if (!validTypes.includes(file.type)) {
        if (window.showToast) {
          window.showToast('error', 'Invalid File Type', 'Please upload a valid image (JPG, JPEG, PNG, or WEBP).');
        } else {
          alert('Please upload a valid image file (JPG, JPEG, PNG, or WEBP).');
        }
        fileInput.value = '';
        return;
      }

      // Check file size (max 15MB)
      if (file.size > 15 * 1024 * 1024) {
        if (window.showToast) {
          window.showToast('error', 'File Too Large', 'Maximum allowed photo size is 15MB.');
        } else {
          alert('Photo size exceeds 15MB limit.');
        }
        fileInput.value = '';
        return;
      }

      // Display preview & meta
      const reader = new FileReader();
      reader.onload = (event) => {
        previewImg.src = event.target.result;
        filenameLabel.textContent = `${file.name} • ${formatFileSize(file.size)}`;
        promptState.style.display = 'none';
        previewState.style.display = 'flex';
        if (errorText) errorText.style.display = 'none';
        container.style.borderColor = 'rgba(34, 197, 94, 0.5)';
        container.classList.add('has-image');
        updateStepProgress();
      };
      reader.readAsDataURL(file);
    }
  });

  // Drag and Drop support
  ['dragenter', 'dragover'].forEach((eventName) => {
    container.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      container.classList.add('is-dragover');
    });
  });

  ['dragleave', 'drop'].forEach((eventName) => {
    container.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      container.classList.remove('is-dragover');
    });
  });

  container.addEventListener('drop', (e) => {
    const dt = e.dataTransfer;
    const files = dt.files;
    if (files && files[0]) {
      fileInput.files = files;
      const event = new Event('change', { bubbles: true });
      fileInput.dispatchEvent(event);
    }
  });
}

/**
 * Interactive Priority Card Selector
 */
function initPriorityChipSelector() {
  const cards = document.querySelectorAll('.priority-card-btn');
  if (!cards.length) return;

  cards.forEach((card) => {
    const radio = card.querySelector('input[type="radio"]');
    if (radio) {
      radio.addEventListener('change', () => {
        cards.forEach((c) => c.classList.remove('is-selected'));
        if (radio.checked) {
          card.classList.add('is-selected');
        }
      });
    }
  });
}

/**
 * Live Character Counter for Description
 */
function initDescriptionCharCounter() {
  const desc = document.getElementById('description');
  const counter = document.getElementById('descCharCount');
  if (!desc || !counter) return;

  const update = () => {
    const count = desc.value.length;
    counter.textContent = `${count} / 1000`;
    if (count > 900) {
      counter.style.color = '#f87171';
    } else {
      counter.style.color = '#64748b';
    }
  };

  desc.addEventListener('input', update);
  update();
}

/**
 * 4-Step Progress Indicator Synchronization & Section Focus
 */
function updateStepProgress() {
  const cat = document.getElementById('category');
  const desc = document.getElementById('description');
  const blk = document.getElementById('block');
  const photo = document.getElementById('photoInput');

  const node1 = document.getElementById('pnode-1');
  const node2 = document.getElementById('pnode-2');
  const node3 = document.getElementById('pnode-3');
  const node4 = document.getElementById('pnode-4');

  // Step 1: Issue
  const isStep1Done = cat && cat.value && desc && desc.value.trim().length >= 5;
  if (node1) {
    node1.className = isStep1Done ? 'progress-node completed' : 'progress-node active';
  }

  // Step 2: Location
  const isStep2Done = blk && blk.value && blk.value !== '-- Select Block --';
  if (node2) {
    if (isStep2Done) {
      node2.className = 'progress-node completed';
    } else if (isStep1Done) {
      node2.className = 'progress-node active';
    } else {
      node2.className = 'progress-node';
    }
  }

  // Step 3: Evidence
  const isStep3Done = photo && photo.files && photo.files.length > 0;
  if (node3) {
    if (isStep3Done) {
      node3.className = 'progress-node completed';
    } else if (isStep2Done) {
      node3.className = 'progress-node active';
    } else {
      node3.className = 'progress-node';
    }
  }

  // Step 4: Submit
  if (node4) {
    if (isStep1Done && isStep2Done && isStep3Done) {
      node4.className = 'progress-node active';
    } else {
      node4.className = 'progress-node';
    }
  }
}

function initProgressIndicatorTracker() {
  const tracker = document.getElementById('formProgressTracker');
  if (!tracker) return;

  const sectionMap = {
    'pnode-1': document.getElementById('section-issue'),
    'pnode-2': document.getElementById('section-location'),
    'pnode-3': document.getElementById('section-evidence'),
    'pnode-4': document.getElementById('section-priority')
  };

  Object.keys(sectionMap).forEach((nodeId) => {
    const node = document.getElementById(nodeId);
    const targetSection = sectionMap[nodeId];
    if (node && targetSection) {
      node.style.cursor = 'pointer';
      node.addEventListener('click', () => {
        targetSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
        targetSection.classList.add('is-focused-section');
        setTimeout(() => targetSection.classList.remove('is-focused-section'), 1200);
      });
    }
  });

  // Listen to inputs
  const inputs = document.querySelectorAll('#category, #description, #block, #room_no');
  inputs.forEach((input) => {
    input.addEventListener('input', updateStepProgress);
    input.addEventListener('change', updateStepProgress);
  });

  updateStepProgress();
}

/**
 * Form Validation before Submission
 */
function initComplaintFormValidation() {
  const form = document.querySelector('#complaintForm');
  if (!form) return;

  const categorySelect = form.querySelector('#category');
  const descriptionText = form.querySelector('#description');
  const blockSelect = form.querySelector('#block');
  const fileInput = form.querySelector('#photoInput');
  const photoContainer = document.querySelector('#photoUploadContainer');
  const photoErrorText = document.querySelector('#photoErrorText');

  form.addEventListener('submit', (e) => {
    let isValid = true;
    let firstErrorElement = null;

    // 1. Category check
    if (!categorySelect.value || categorySelect.value === 'Select Category' || categorySelect.value === '-- Select Complaint Category --') {
      showFieldError(categorySelect, 'Please select a complaint category.');
      isValid = false;
      if (!firstErrorElement) firstErrorElement = categorySelect;
    } else {
      clearFieldError(categorySelect);
    }

    // 2. Description check
    if (!descriptionText.value.trim()) {
      showFieldError(descriptionText, 'Please provide a detailed description of what happened and what is damaged/wrong.');
      isValid = false;
      if (!firstErrorElement) firstErrorElement = descriptionText;
    } else if (descriptionText.value.trim().length < 5) {
      showFieldError(descriptionText, 'Please provide at least 5 characters describing the issue.');
      isValid = false;
      if (!firstErrorElement) firstErrorElement = descriptionText;
    } else {
      clearFieldError(descriptionText);
    }

    // 3. Mandatory Photo Evidence Check
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      isValid = false;
      if (photoContainer) {
        photoContainer.style.borderColor = '#f43f5e';
      }
      if (photoErrorText) {
        photoErrorText.style.display = 'block';
        photoErrorText.textContent = '⚠ Please upload a photo of the issue before submitting.';
      }
      if (!firstErrorElement) firstErrorElement = photoContainer;
    } else {
      if (photoErrorText) photoErrorText.style.display = 'none';
      if (photoContainer) photoContainer.style.borderColor = 'rgba(34, 197, 94, 0.5)';
    }

    // 4. Block / Location check
    if (!blockSelect.value || blockSelect.value === 'Select Block' || blockSelect.value === '-- Select Block --' || blockSelect.value === '-- Select Location / Block --') {
      showFieldError(blockSelect, 'Please select the campus location/block where the issue is located.');
      isValid = false;
      if (!firstErrorElement) firstErrorElement = blockSelect;
    } else {
      clearFieldError(blockSelect);
    }

    if (!isValid) {
      e.preventDefault();
      if (firstErrorElement) {
        firstErrorElement.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }
      if (window.showToast) {
        if (!fileInput.files || fileInput.files.length === 0) {
          window.showToast('error', 'Photo Required', 'Please upload a photo of the issue before submitting.');
        } else {
          window.showToast('error', 'Incomplete Form', 'Please fill in all required fields marked with *');
        }
      }
    }
  });

  // Clear errors on input
  [categorySelect, descriptionText, blockSelect].forEach((el) => {
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
    feedback.style.color = '#f43f5e';
    feedback.style.fontSize = '0.8rem';
    feedback.style.marginTop = '0.35rem';
    group.appendChild(feedback);
  }
  feedback.textContent = errorMessage;
}

function clearFieldError(inputElement) {
  const group = inputElement.closest('.form-group');
  if (!group) return;
  group.classList.remove('has-error');
  const feedback = group.querySelector('.form-error-feedback');
  if (feedback) feedback.remove();
}

/**
 * Automatically sets the Location dropdown when passed via URL query parameters
 */
function initLocationParamAutoSelect() {
  const params = new URLSearchParams(window.location.search);
  const rawLoc = params.get('location') || params.get('block');
  if (!rawLoc) return;

  const blockSelect = document.getElementById('block') || document.querySelector('select[name="block"], select[name="location"]');
  if (!blockSelect) return;

  const norm = rawLoc.replace(/[-_]/g, ' ').trim().toLowerCase();
  for (let i = 0; i < blockSelect.options.length; i++) {
    const opt = blockSelect.options[i];
    if (!opt.value) continue;
    const optVal = opt.value.toLowerCase();
    if (optVal === norm || optVal.includes(norm) || norm.includes(optVal)) {
      blockSelect.selectedIndex = i;
      // Trigger change event to clear errors or sync any watchers
      blockSelect.dispatchEvent(new Event('change', { bubbles: true }));
      break;
    }
  }
}



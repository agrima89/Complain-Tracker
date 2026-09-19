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
  initSmartComplaintAssist();
  initSimilarComplaintDetection();
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

/**
 * 1. Smart Complaint Detection - Real-time client-side assist
 */
function initSmartComplaintAssist() {
  const descTextarea = document.getElementById('description');
  const panel = document.getElementById('smartAssistPanel');
  const catVal = document.getElementById('smartCatVal');
  const prioVal = document.getElementById('smartPrioVal');
  const locVal = document.getElementById('smartLocVal');
  const reasonText = document.getElementById('smartReasonText');
  const confidencePill = document.getElementById('smartConfidencePill');
  const applyBtn = document.getElementById('applySmartSuggestionsBtn');

  if (!descTextarea || !panel) return;

  let debounceTimer = null;
  let latestAnalysis = null;

  const categoryIcons = {
    'Electrical': '⚡ Electrical',
    'Cleaning': '🚰 Cleaning / Water',
    'Hostel': '🏢 Hostel',
    'Wi-Fi/Internet': '💻 Wi-Fi / Internet',
    'Classroom': '🏫 Classroom',
    'Library': '📚 Library',
    'Infrastructure': '🏗️ Infrastructure',
    'Other': '📁 Other'
  };

  descTextarea.addEventListener('input', () => {
    const text = descTextarea.value.trim();
    clearTimeout(debounceTimer);

    if (text.length < 8) {
      panel.style.display = 'none';
      latestAnalysis = null;
      return;
    }

    debounceTimer = setTimeout(async () => {
      try {
        const response = await fetch('/api/smart-detect', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-Requested-With': 'XMLHttpRequest'
          },
          body: JSON.stringify({ text: text })
        });

        if (!response.ok) return;
        const data = await response.json();

        if (data.success) {
          latestAnalysis = data;

          // Category display
          if (catVal) {
            catVal.textContent = categoryIcons[data.category] || `📁 ${data.category}`;
          }

          // Priority display
          if (prioVal) {
            const prioColors = {
              'High': '<span style="color: #f87171;">🔴 High Priority</span>',
              'Medium': '<span style="color: #fbbf24;">🟡 Medium Priority</span>',
              'Low': '<span style="color: #38bdf8;">🟢 Low Priority</span>'
            };
            prioVal.innerHTML = prioColors[data.priority] || data.priority;
          }

          // Location display
          if (locVal) {
            locVal.textContent = data.location_label ? `🏢 ${data.location_label}` : (data.location_block ? `📍 ${data.location_block}` : '🏢 Campus Premises');
          }

          // Reason display
          if (reasonText) {
            reasonText.textContent = `"${data.reason}"`;
          }

          // Confidence display
          if (confidencePill) {
            const pct = Math.round(data.confidence * 100);
            confidencePill.textContent = `⚡ ${pct}% Confidence`;
          }

          panel.style.display = 'block';
          panel.classList.add('animate-pop-in');
        }
      } catch (err) {
        console.warn('Smart assist detection note:', err);
      }
    }, 280);
  });

  // Apply Suggestions click handler
  if (applyBtn) {
    applyBtn.addEventListener('click', () => {
      if (!latestAnalysis) return;

      let appliedCount = 0;

      // 1. Auto-select Category
      const catSelect = document.getElementById('category');
      if (catSelect && latestAnalysis.category) {
        for (let i = 0; i < catSelect.options.length; i++) {
          if (catSelect.options[i].value === latestAnalysis.category) {
            catSelect.selectedIndex = i;
            catSelect.dispatchEvent(new Event('change', { bubbles: true }));
            catSelect.classList.add('highlight-assist-pulse');
            setTimeout(() => catSelect.classList.remove('highlight-assist-pulse'), 1500);
            appliedCount++;
            break;
          }
        }
      }

      // 2. Auto-select Priority
      if (latestAnalysis.priority) {
        const targetRadio = document.querySelector(`input[name="priority"][value="${latestAnalysis.priority}"]`);
        if (targetRadio) {
          targetRadio.checked = true;
          document.querySelectorAll('.priority-card-btn').forEach((card) => card.classList.remove('is-selected'));
          const parentCard = targetRadio.closest('.priority-card-btn');
          if (parentCard) {
            parentCard.classList.add('is-selected');
            parentCard.classList.add('highlight-assist-pulse');
            setTimeout(() => parentCard.classList.remove('highlight-assist-pulse'), 1500);
          }
          appliedCount++;
        }
      }

      // 3. Auto-select Location / Block
      const blockSelect = document.getElementById('block');
      if (blockSelect && latestAnalysis.location_block) {
        for (let i = 0; i < blockSelect.options.length; i++) {
          if (blockSelect.options[i].value.toLowerCase() === latestAnalysis.location_block.toLowerCase()) {
            blockSelect.selectedIndex = i;
            blockSelect.dispatchEvent(new Event('change', { bubbles: true }));
            blockSelect.classList.add('highlight-assist-pulse');
            setTimeout(() => blockSelect.classList.remove('highlight-assist-pulse'), 1500);
            appliedCount++;
            break;
          }
        }
      }

      // Visual feedback
      const originalText = applyBtn.innerHTML;
      applyBtn.innerHTML = '<span>✓</span> Suggestions Applied!';
      applyBtn.style.background = 'linear-gradient(135deg, #059669, #047857)';
      setTimeout(() => {
        applyBtn.innerHTML = originalText;
        applyBtn.style.background = '';
      }, 2000);

      if (window.showToast) {
        window.showToast('info', 'Smart Assist Applied', `Auto-populated Category (${latestAnalysis.category}), Priority (${latestAnalysis.priority})${latestAnalysis.location_block ? ` & Location (${latestAnalysis.location_block})` : ''}.`);
      }
    });
  }
}

/**
 * 2. Similar / Duplicate Complaint Detection - Pre-submission check
 */
function initSimilarComplaintDetection() {
  const form = document.querySelector('#complaintForm');
  const alertPanel = document.getElementById('similarComplaintAlert');
  const cardsList = document.getElementById('similarComplaintsList');
  const countText = document.getElementById('similarCountText');
  const matchBadge = document.getElementById('similarMatchBadge');
  const toggleBtn = document.getElementById('toggleSimilarDetailsBtn');
  const toggleBtnText = document.getElementById('toggleSimilarBtnText');
  const submitAnywayBtn = document.getElementById('submitAnywayBtn');

  if (!form || !alertPanel) return;

  let allowSubmitAnyway = false;

  // Intercept Form Submit to check similarity
  form.addEventListener('submit', async (e) => {
    if (allowSubmitAnyway) {
      return; // Proceed with submission
    }

    const descTextarea = form.querySelector('#description');
    const catSelect = form.querySelector('#category');
    const blockSelect = form.querySelector('#block');

    if (!descTextarea || descTextarea.value.trim().length < 8) return;

    // Check if photo is provided first (standard validation)
    const fileInput = form.querySelector('#photoInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      return; // Let standard validation flag photo
    }

    e.preventDefault();

    try {
      const response = await fetch('/api/check-similar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-Requested-With': 'XMLHttpRequest'
        },
        body: JSON.stringify({
          description: descTextarea.value.trim(),
          category: catSelect ? catSelect.value : '',
          block: blockSelect ? blockSelect.value : ''
        })
      });

      if (!response.ok) {
        allowSubmitAnyway = true;
        form.requestSubmit();
        return;
      }

      const data = await response.json();

      if (data.found && data.similar && data.similar.length > 0) {
        // Render Similar Complaints Cards
        renderSimilarComplaints(data.similar);
        
        if (countText) {
          countText.textContent = `We found ${data.count} similar unresolved complaint${data.count > 1 ? 's' : ''} recently reported in this area.`;
        }

        if (matchBadge) {
          matchBadge.textContent = `${data.similar[0].similarity}% Keyword Similarity`;
        }

        alertPanel.style.display = 'block';
        alertPanel.scrollIntoView({ behavior: 'smooth', block: 'center' });
        alertPanel.classList.add('animate-shake-attention');
        setTimeout(() => alertPanel.classList.remove('animate-shake-attention'), 800);
      } else {
        // No duplicate found -> Submit seamlessly
        allowSubmitAnyway = true;
        form.requestSubmit();
      }
    } catch (err) {
      console.warn('Similarity check bypassed due to network note:', err);
      allowSubmitAnyway = true;
      form.requestSubmit();
    }
  });

  // "Submit Anyway" button click
  if (submitAnywayBtn) {
    submitAnywayBtn.addEventListener('click', () => {
      allowSubmitAnyway = true;
      form.requestSubmit();
    });
  }

  // Toggle details button
  if (toggleBtn) {
    toggleBtn.addEventListener('click', () => {
      if (cardsList) {
        const isCollapsed = cardsList.classList.contains('is-collapsed');
        if (isCollapsed) {
          cardsList.classList.remove('is-collapsed');
          if (toggleBtnText) toggleBtnText.textContent = 'Collapse Similar Issues';
        } else {
          cardsList.classList.add('is-collapsed');
          if (toggleBtnText) toggleBtnText.textContent = 'View Similar Complaints';
        }
      }
    });
  }

  function renderSimilarComplaints(complaints) {
    if (!cardsList) return;
    cardsList.innerHTML = '';

    complaints.forEach((c) => {
      const card = document.createElement('div');
      card.className = 'similar-item-card';

      const prioColor = c.priority === 'High' ? '#f87171' : (c.priority === 'Medium' ? '#fbbf24' : '#38bdf8');
      const statusColor = c.status === 'In Progress' ? '#38bdf8' : '#fbbf24';

      card.innerHTML = `
        <div class="similar-item-header">
          <div style="display: flex; align-items: center; gap: 0.5rem; flex-wrap: wrap;">
            <span class="similar-item-ticket">${c.ticket_id}</span>
            <span class="badge" style="background: rgba(15, 23, 42, 0.6); color: #cbd5e1; font-size: 0.75rem;">${c.category}</span>
            <span style="color: #94a3b8; font-size: 0.8rem;">📍 ${c.location}</span>
          </div>
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <span class="badge" style="background: rgba(245, 158, 11, 0.15); color: ${statusColor}; border: 1px solid rgba(245, 158, 11, 0.3); font-size: 0.725rem;">
              ● ${c.status}
            </span>
            <span style="font-size: 0.75rem; color: #94a3b8;">📅 ${c.date_note || c.date}</span>
          </div>
        </div>
        <p class="similar-item-snippet">"${c.snippet}"</p>
      `;

      cardsList.appendChild(card);
    });
  }
}



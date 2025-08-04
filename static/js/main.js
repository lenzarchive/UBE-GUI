// -*- coding: utf-8 -*-
/**
 * UnityBundleExtractor - Main Frontend JavaScript
 * Author: lenzarchive (https://github.com/lenzarchive)
 * License: MIT License
 *
 * This script handles the client-side interactions for the Unity asset bundle extractor web interface.
 * It manages file uploads, displays processing status, renders asset lists, and initiates asset extraction.
 */

class UnityBundleExtractor {
    /**
     * Initializes the UnityBundleExtractor application.
     * Sets up internal state, references DOM elements, and registers event listeners.
     */
    constructor() {
        console.log('UnityBundleExtractor: Constructor called.');
        this.currentSessionId = null;
        this.bundleMetadata = null;
        this.selectedAssets = new Set();
        this.isProcessing = false; // General processing flag for upload button
        this.statusPollingInterval = null;
        this.extractionPollingInterval = null;
        this.allSelectedFiles = [];

        /**
         * References to key DOM elements for easy access.
         * @type {object}
         */
        this.elements = {
            uploadForm: document.getElementById('upload-form'),
            fileInput: document.getElementById('file-input'),
            customFileUploadText: document.getElementById('custom-file-upload-text'),
            
            optionalUploadSection: document.getElementById('optional-upload-section'),
            optionalFileInput: document.getElementById('optional-file-input'),
            optionalFileUploadText: document.getElementById('optional-file-upload-text'),
            additionalFilesList: document.getElementById('additional-files-list'),

            uploadButton: document.getElementById('upload-button'),
            progressBar: document.getElementById('progress-bar'),
            progressBarInner: document.getElementById('progress-bar-inner'),
            resultsSection: document.getElementById('results-section'),
            metadataInfo: document.getElementById('metadata-info'),
            assetListContainer: document.getElementById('asset-list-container'),
            filterInput: document.getElementById('filter-input'),
            selectAllButton: document.getElementById('select-all-button'),
            deselectAllButton: document.getElementById('deselect-all-button'),
            extractButton: document.getElementById('extract-button'),
            statusMessage: document.getElementById('status-message'),
            
            errorInfoCard: document.getElementById('error-info-card'),
            errorInfoContent: document.getElementById('error-info-content'),

            sendLogCheckbox: document.getElementById('send-log-checkbox'),
            allowStorageCheckbox: document.getElementById('allow-storage-checkbox'),
            btcLink: document.getElementById('btc-link'),
            btcAddress: document.getElementById('btc-address'),
            assetClassesCard: document.getElementById('asset-classes-card'),
            assetClassesList: document.getElementById('asset-classes-list'),

            queueInfo: document.getElementById('queue-info'), // Element for queue information
            queueControls: document.getElementById('queue-controls'), // Queue control buttons container
            cancelQueueButton: document.getElementById('cancel-queue-button'), // Cancel button

            // Modal elements
            customConfirmModal: document.getElementById('custom-confirm-modal'),
            modalTitle: document.getElementById('modal-title'),
            modalMessage: document.getElementById('modal-message'),
            modalConfirmButton: document.getElementById('modal-confirm-button'),
            modalCancelButton: document.getElementById('modal-cancel-button'),
        };
        
        this.initializeEventListeners();
        this.initializeBTCAddressToggle();
        console.log('UnityBundleExtractor: Initialization complete.');
    }
    
    /**
     * Sets up all necessary event listeners for user interactions.
     * Includes form submission, file input changes, drag-and-drop, and button clicks.
     */
    initializeEventListeners() {
        console.log('UnityBundleExtractor: Initializing event listeners...');
        // Global drag-drop handlers for body (to prevent browser opening file)
        document.body.addEventListener('dragover', (e) => e.preventDefault());
        document.body.addEventListener('dragleave', (e) => e.preventDefault());
        document.body.addEventListener('drop', (e) => e.preventDefault());

        this.elements.uploadForm.addEventListener('submit', (e) => {
            e.preventDefault();
            this.handleFileUpload();
            console.log('Event: Upload form submitted.');
        });
        
        this.elements.selectAllButton.addEventListener('click', () => this.selectAllAssets());
        this.elements.deselectAllButton.addEventListener('click', () => this.deselectAllAssets());
        this.elements.filterInput.addEventListener('input', () => this.filterAssets());
        this.elements.extractButton.addEventListener('click', () => this.handleAssetExtraction());
        
        this.elements.fileInput.addEventListener('change', (e) => {
            this.handlePrimaryFileInput(e.target.files);
            console.log('Event: Primary file input changed.');
        });
        this.elements.optionalFileInput.addEventListener('change', (e) => {
            this.handleOptionalFileInput(e.target.files);
            console.log('Event: Optional file input changed.');
        });

        // Prevents default form submission on filter input's Enter keypress
        this.elements.filterInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                console.log('Event: Filter input Enter keypress prevented default.');
            }
        });

        // Drag-and-drop functionality for primary file input
        const customFileUploadLabel = document.querySelector('.custom-file-upload-label');
        if (customFileUploadLabel) {
            customFileUploadLabel.addEventListener('dragover', (e) => {
                e.preventDefault(); 
                e.stopPropagation(); 
                customFileUploadLabel.classList.add('drag-over'); 
                console.log('Event: Main D&D dragover.');
            });

            customFileUploadLabel.addEventListener('dragleave', (e) => {
                customFileUploadLabel.classList.remove('drag-over');
                console.log('Event: Main D&D dragleave.');
            });

            customFileUploadLabel.addEventListener('drop', (e) => {
                e.preventDefault(); 
                e.stopPropagation(); 
                customFileUploadLabel.classList.remove('drag-over');
                this.handlePrimaryFileInput(e.dataTransfer.files); 
                console.log('Event: Main D&D drop, files:', e.dataTransfer.files);
            });
        }

        // Drag-and-drop functionality for optional file input
        const optionalUploadLabel = document.getElementById('optional-upload-area');
        if (optionalUploadLabel) {
            optionalUploadLabel.addEventListener('dragover', (e) => {
                e.preventDefault();
                e.stopPropagation(); 
                optionalUploadLabel.classList.add('drag-over');
                console.log('Event: Optional D&D dragover.');
            });

            optionalUploadLabel.addEventListener('dragleave', (e) => {
                optionalUploadLabel.classList.remove('drag-over');
                console.log('Event: Optional D&D dragleave.');
            });

            optionalUploadLabel.addEventListener('drop', (e) => {
                e.preventDefault();
                e.stopPropagation(); 
                optionalUploadLabel.classList.remove('drag-over');
                this.handleOptionalFileInput(e.dataTransfer.files); 
                console.log('Event: Optional D&D drop, files:', e.dataTransfer.files);
            });
        }

        // Event delegation for asset list item clicks to toggle checkboxes
        this.elements.assetListContainer.addEventListener('click', (e) => {
            const listItem = e.target.closest('li');
            if (listItem) {
                const checkbox = listItem.querySelector('input[type="checkbox"]');
                if (checkbox && e.target.type !== 'checkbox') {
                    checkbox.checked = !checkbox.checked;
                    this.toggleAssetSelection(parseInt(checkbox.dataset.assetIndex, 10), checkbox.checked);
                    console.log('Event: Asset list item clicked, checkbox toggled.');
                }
            }
        });

        // Event delegation for removing additional files
        this.elements.additionalFilesList.addEventListener('click', (e) => {
            if (e.target.classList.contains('remove-file-btn')) {
                const globalIndexToRemove = parseInt(e.target.dataset.globalIndex, 10);
                if (!isNaN(globalIndexToRemove) && globalIndexToRemove >= 0 && globalIndexToRemove < this.allSelectedFiles.length) {
                    this.allSelectedFiles.splice(globalIndexToRemove, 1);
                    this.updateFileUploadUI();
                    // Re-evaluate if a main file is still present after removal
                    const hasMainFile = this.allSelectedFiles.some(file => {
                        const ext = file.name.split('.').pop().toLowerCase();
                        return ['bundle', 'unity3d', 'assets', 'unitybundle', 'assetbundle'].includes(ext);
                    });
                    this.elements.uploadButton.disabled = (this.allSelectedFiles.length === 0 || !hasMainFile || this.isProcessing);
                    console.log(`Event: Removed file at index ${globalIndexToRemove}. Current files:`, this.allSelectedFiles.map(f => f.name));
                }
            }
        });

        // Event delegation for checkbox changes in asset list
        this.elements.assetListContainer.addEventListener('change', (e) => {
             if (e.target.matches('input[type="checkbox"].asset-checkbox')) {
                this.toggleAssetSelection(parseInt(e.target.dataset.assetIndex, 10), e.target.checked);
                console.log('Event: Asset checkbox changed.');
            } else if (e.target.matches('input[type="checkbox"].category-checkbox')) {
                this.toggleCategorySelection(e.target.dataset.category, e.target.checked);
                console.log('Event: Category checkbox changed.');
            }
        });

        // Queue control buttons
        this.elements.cancelQueueButton.addEventListener('click', () => this.handleQueueAction('cancel'));

        // Modal button event listeners
        this.elements.modalConfirmButton.addEventListener('click', () => {
            if (this._modalResolve) {
                this._modalResolve(true); // "Stop" button confirms the action (stop)
            }
            this._hideConfirmModal();
            console.log('Event: Modal Confirm (Stop) button clicked.');
        });

        this.elements.modalCancelButton.addEventListener('click', () => {
            if (this._modalResolve) {
                this._modalResolve(false); // "Continue" button cancels the action (continue)
            }
            this._hideConfirmModal();
            console.log('Event: Modal Cancel (Continue) button clicked.');
        });

        console.log('UnityBundleExtractor: Event listeners initialized.');
    }

    /**
     * Shows a custom confirmation modal dialog.
     * @param {string} title - The title of the modal.
     * @param {string} message - The message to display in the modal.
     * @returns {Promise<boolean>} A promise that resolves to true if 'Stop' is clicked, false if 'Continue'.
     */
    showConfirmModal(title, message) {
        return new Promise(resolve => {
            this._modalResolve = resolve; // Store the resolve function for later use
            this.elements.modalTitle.textContent = title;
            this.elements.modalMessage.textContent = message;
            this.elements.customConfirmModal.style.display = 'flex'; // Show modal
            console.log('Function: showConfirmModal called. Modal displayed.');
        });
    }

    /** Hides the custom confirmation modal dialog. */
    _hideConfirmModal() {
        this.elements.customConfirmModal.style.display = 'none'; // Hide modal
        this._modalResolve = null; // Clear the stored resolve function
        console.log('Function: _hideConfirmModal called. Modal hidden.');
    }

    /**
     * Handles file input from the primary upload area.
     * Filters for valid main Unity bundle/asset files and updates the file list.
     * @param {FileList} files - The FileList object from the input event.
     */
    handlePrimaryFileInput(files) {
        console.log('Function: handlePrimaryFileInput called with files:', files);
        this.allSelectedFiles = []; // Clear previous selection
        let mainFileDetected = false;
        let validFiles = [];

        if (files.length > 0) {
            for (let i = 0; i < files.length; i++) {
                const file = files[i];
                if (this.isValidMainFileType(file.name)) {
                    if (!mainFileDetected) {
                        this.allSelectedFiles.push(file);
                        mainFileDetected = true;
                    } else {
                        validFiles.push(file);
                    }
                } else if (this.isValidOptionalFileType(file.name) && file.size > 0) {
                    validFiles.push(file);
                } else {
                    this.showStatusMessage(`Invalid or empty file detected: ${file.name}.`, 'error');
                    console.warn(`handlePrimaryFileInput: Invalid or empty file detected: ${file.name}`);
                }
            }
        }
        this.allSelectedFiles.push(...validFiles);

        this.updateFileUploadUI();
        this.elements.uploadButton.disabled = (this.allSelectedFiles.length === 0 || !mainFileDetected || this.isProcessing);
        
        this.elements.optionalUploadSection.style.display = mainFileDetected ? 'block' : 'none';
        this.hideErrorCard();
        console.log('handlePrimaryFileInput: UI updated. Main file detected:', mainFileDetected, 'Upload button disabled:', this.elements.uploadButton.disabled);
    }

    /**
     * Handles file input from the optional upload area.
     * Adds valid optional files to the overall selection and updates the UI.
     * @param {FileList} files - The FileList object from the input event.
     */
    handleOptionalFileInput(files) {
        console.log('Function: handleOptionalFileInput called with files:', files);
        let newValidFiles = [];
        for (let i = 0; i < files.length; i++) {
            const file = files[i];
            if (this.isValidOptionalFileType(file.name) && file.size > 0) { 
                if (!this.allSelectedFiles.some(f => f.name === file.name && f.size === file.size)) {
                    newValidFiles.push(file);
                }
            } else {
                const errorMessage = `Empty or invalid file detected: ${file.name}. Please upload valid files.`;
                this.showStatusMessage(errorMessage, 'error');
                console.warn(`handleOptionalFileInput: Invalid or empty file detected: ${file.name}`);
            }
        }
        
        this.allSelectedFiles.push(...newValidFiles); 
        this.updateFileUploadUI(); 
        this.elements.uploadButton.disabled = (this.allSelectedFiles.length === 0 || this.isProcessing);
        this.hideErrorCard(); 
        
        if (newValidFiles.length > 0) {
            this.showStatusMessage(`Successfully added ${newValidFiles.length} optional file(s).`, 'success', 3000);
            console.log(`handleOptionalFileInput: Added ${newValidFiles.length} new optional file(s).`);
        } else if (files.length > 0) {
            this.showStatusMessage(`No new optional files added (might be duplicates or empty).`, 'warning', 3000);
            console.log('handleOptionalFileInput: No new optional files added.');
        }
    }

    /**
     * Updates the UI to reflect the currently selected files for upload.
     * Displays the primary file name and lists additional files.
     */
    updateFileUploadUI() {
        console.log('Function: updateFileUploadUI called.');
        const primaryFiles = this.allSelectedFiles.filter(file => this.isValidMainFileType(file.name));
        const displayedPrimaryFile = primaryFiles.length > 0 ? primaryFiles[0] : null;

        const additionalFiles = this.allSelectedFiles.filter(file => !primaryFiles.includes(file));

        if (displayedPrimaryFile) {
            this.elements.customFileUploadText.textContent = displayedPrimaryFile.name;
        } else {
            this.elements.customFileUploadText.textContent = 'Drag & Drop or Choose Unity Main File(s) (.bundle, .unity3d, .assets, .unitybundle)';
        }

        this.elements.additionalFilesList.innerHTML = '';
        if (additionalFiles.length > 0) {
            additionalFiles.forEach((file, index) => {
                const li = document.createElement('li');
                const globalIndex = this.allSelectedFiles.indexOf(file);
                li.innerHTML = `<span>- ${this.escapeHtml(file.name)}</span> <span class="remove-file-btn" data-global-index="${globalIndex}">x</span>`;
                this.elements.additionalFilesList.appendChild(li);
            });
            this.elements.optionalFileUploadText.textContent = `Selected ${additionalFiles.length} additional file(s)`;
        } else {
            this.elements.optionalFileUploadText.textContent = 'Drag & Drop any additional resource files here (optional)';
        }

        if (displayedPrimaryFile && this.elements.statusMessage.className !== 'status-message error') {
             this.hideStatusMessage();
        } else if (this.allSelectedFiles.length === 0) {
            this.hideStatusMessage(); 
        }
        console.log('updateFileUploadUI: UI updated. Primary file:', displayedPrimaryFile ? displayedPrimaryFile.name : 'None', 'Additional files count:', additionalFiles.length);
    }
    
    /**
     * Configures the toggle and copy functionality for the BTC address display.
     */
    initializeBTCAddressToggle() {
        const btcAddress = "bc1q0ay7shy6zyy3xduf9hgsgu5crfzvpes93d48a6"; 
        const btcLink = this.elements.btcLink;
        const btcAddressSpan = this.elements.btcAddress;

        if (!btcLink || !btcAddressSpan) return;

        /**
         * Copies text to the clipboard.
         * @param {string} text - The text to copy.
         * @returns {Promise<void>} A promise that resolves if copy is successful.
         */
        const copyToClipboard = (text) => {
            if (navigator.clipboard && window.isSecureContext) {
                return navigator.clipboard.writeText(text);
            } else {
                return new Promise((resolve, reject) => {
                    const textArea = document.createElement('textarea');
                    textArea.value = text;
                    textArea.style.position = 'absolute';
                    textArea.style.left = '-9999px';
                    document.body.appendChild(textArea);
                    textArea.select();
                    try {
                        document.execCommand('copy');
                        resolve();
                    } catch (err) {
                        reject(err);
                    } finally {
                        document.body.removeChild(textArea);
                    }
                });
            }
        };

        btcLink.addEventListener('click', (e) => {
            e.preventDefault();
            const isHidden = btcAddressSpan.style.display === 'none' || !btcAddressSpan.style.display;
            if (isHidden) {
                btcAddressSpan.textContent = btcAddress;
                btcAddressSpan.style.display = 'block';
                btcAddressSpan.style.cursor = 'pointer';
            } else {
                btcAddressSpan.style.display = 'none';
            }
            console.log('Event: BTC link clicked, visibility toggled.');
        });

        btcAddressSpan.addEventListener('click', () => {
            copyToClipboard(btcAddress).then(() => {
                const originalText = btcAddress;
                btcAddressSpan.textContent = 'Copied!';
                setTimeout(() => {
                    btcAddressSpan.textContent = originalText;
                }, 1500);
                console.log('Event: BTC address copied.');
            }).catch(err => {
                console.error('Event: Failed to copy BTC address: ', err);
                btcAddressSpan.textContent = 'Copy Failed!';
                setTimeout(() => {
                    btcAddressSpan.textContent = btcAddress;
                }, 1500);
            });
        });
    }
    
    /**
     * Checks if a filename has an allowed primary Unity file extension.
     * @param {string} filename - The name of the file.
     * @returns {boolean} True if the extension is allowed, False otherwise.
     */
    isValidMainFileType(filename) {
        const allowedExtensions = ['bundle', 'unity3d', 'assets', 'unitybundle', 'assetbundle']; 
        const extension = filename.split('.').pop().toLowerCase();
        return allowedExtensions.includes(extension);
    }

    /**
     * Checks if a filename is valid for optional file upload (non-empty).
     * More specific validation (e.g., .resS) would occur on the server.
     * @param {string} filename - The name of the file.
     * @returns {boolean} True if the filename is not empty, False otherwise.
     */
    isValidOptionalFileType(filename) {
        return filename && filename.trim() !== ''; 
    }
    
    /**
     * Handles the file upload process to the server.
     * Submits selected files via FormData and initiates status polling.
     */
    async handleFileUpload() {
        console.log('Function: handleFileUpload called.');
        if (this.allSelectedFiles.length === 0) {
            const errorMessage = 'Please select at least one file to upload.';
            this.showStatusMessage(errorMessage, 'error');
            this.displayErrorCard(errorMessage);
            console.error('handleFileUpload: No files selected, returning.');
            return;
        }
        
        const hasMainFile = this.allSelectedFiles.some(file => this.isValidMainFileType(file.name));

        if (!hasMainFile) {
            const errorMessage = 'No main Unity bundle/asset file (.bundle, .unity3d, .assets) found among selected files. Please include at least one.';
            this.showStatusMessage(errorMessage, 'error');
            this.displayErrorCard(errorMessage); 
            console.error('handleFileUpload: No main file detected, returning.');
            return;
        }

        let totalSize = this.allSelectedFiles.reduce((sum, file) => sum + file.size, 0);
        const maxSize = 500 * 1024 * 1024; // 500 MB
        if (totalSize > maxSize) {
            const errorMessage = 'Total file size too large (Max 500MB).';
            this.showStatusMessage(errorMessage, 'error');
            this.displayErrorCard(errorMessage);
            console.error('handleFileUpload: Total file size too large, returning.');
            return;
        }

        try {
            this.setProcessingState(true, 'queued'); // Set state to queued immediately
            console.log('handleFileUpload: Processing state set to queued.');
            const formData = new FormData(); 

            this.allSelectedFiles.forEach(file => formData.append('files', file));
            
            // Append checkbox states to FormData
            const sendLogCheckbox = this.elements.sendLogCheckbox;
            if (sendLogCheckbox) {
                formData.append('send_log', sendLogCheckbox.checked ? 'true' : 'false');
            }

            const allowStorageCheckbox = this.elements.allowStorageCheckbox;
            if (allowStorageCheckbox) {
                formData.append('allow_storage', allowStorageCheckbox.checked ? 'true' : 'false'); 
            }
            
            console.log('handleFileUpload: Sending /api/upload request.');
            const response = await fetch('/api/upload', { method: 'POST', body: formData });
            
            const responseText = await response.text(); 
            console.log('handleFileUpload: Received /api/upload response (raw text):', responseText);

            if (!response.ok) {
                // Handle 429 Too Many Requests specifically
                if (response.status === 429) {
                    const errorJson = JSON.parse(responseText);
                    const retryAfter = response.headers.get('Retry-After') || 30;
                    const rateLimitMessage = errorJson.error + ` Please try again in ${retryAfter} seconds.`;
                    this.showStatusMessage(rateLimitMessage, 'error');
                    this.displayErrorCard(rateLimitMessage);
                    this.setProcessingState(false);
                    console.warn('handleFileUpload: Rate limit exceeded (429).');
                    return;
                }
                throw new Error(responseText || 'Upload failed');
            }
            
            let result;
            try {
                result = JSON.parse(responseText); 
            } catch (jsonError) {
                console.error('handleFileUpload: Failed to parse /api/upload response as JSON:', jsonError, responseText);
                throw new Error('Invalid JSON response from server: ' + responseText);
            }

            this.currentSessionId = result.session_id;
            this.startStatusPolling();
            this.hideErrorCard(); 
            
            if (result.status === 'queued') {
                this.updateQueueInfo(result.queue_position, result.total_queue_size);
                this.showStatusMessage('File uploaded. Added to processing queue.', 'info');
                this.elements.queueControls.style.display = 'flex';
                console.log('handleFileUpload: Task queued, showing queue info and controls.');
            }
            
        } catch (error) {
            console.error('handleFileUpload: Error in try-catch block:', error);
            this.handleError(error, 'Upload failed');
        }
    }
    
    /**
     * Starts polling the server for analysis status updates.
     * Updates progress bar, displays queue position, and handles completion or error states.
     */
    startStatusPolling() {
        this.stopPolling('status');
        console.log('Function: startStatusPolling called for session:', this.currentSessionId);
        this.statusPollingInterval = setInterval(async () => {
            try {
                console.log('startStatusPolling: Fetching status for session:', this.currentSessionId);
                const response = await fetch(`/api/status/${this.currentSessionId}`);
                const responseText = await response.text();
                
                if (!response.ok) {
                    console.error('startStatusPolling: Status check failed with status:', response.status, response.statusText, responseText);
                    throw new Error(responseText || 'Status check failed');
                }
                
                let status;
                try {
                    status = JSON.parse(responseText);
                } catch (jsonError) {
                    console.error('startStatusPolling: Failed to parse /api/status response as JSON:', jsonError, responseText);
                    throw new Error('Invalid JSON response from server during status check: ' + responseText);
                }
                
                console.log('startStatusPolling: Received status response:', status);
                
                // Update queue info if still queued or being analyzed
                if (status.status === 'queued' || status.status === 'analyzing') {
                    this.updateQueueInfo(status.queue_position, status.total_queue_size);
                    this.elements.queueControls.style.display = 'flex';
                    console.log('startStatusPolling: Status is queued/analyzing, updating queue info.');
                } else {
                    this.hideQueueInfo();
                    this.elements.queueControls.style.display = 'none';
                    console.log('startStatusPolling: Status is not queued/analyzing, hiding queue info and controls.');
                }

                this.updateProgress(status.progress || 0);
                
                if (status.status === 'completed') {
                    if (status.metadata && status.metadata.bundle_info && status.metadata.assets && status.metadata.asset_classes) {
                        console.log('startStatusPolling: Analysis completed successfully, metadata received.');
                        this.stopPolling('status');
                        this.handleAnalysisComplete(status.metadata);
                    } else {
                        console.error('startStatusPolling: Analysis reported completed, but metadata is incomplete or malformed.');
                        this.stopPolling('status');
                        const errorMessage = "Analysis reported as completed, but received incomplete or malformed metadata from the server. Please try again or check server logs.";
                        this.displayErrorCard(errorMessage);
                        this.setProcessingState(false);
                    }
                } else if (status.status === 'error') {
                    console.error('startStatusPolling: Analysis reported error:', status.error);
                    this.stopPolling('status');
                    let errorMessage = status.error || 'Analysis failed on server';
                    if (typeof errorMessage === 'object' && errorMessage.error) {
                        errorMessage = errorMessage.error; 
                    }
                    this.displayErrorCard(errorMessage); 
                    this.setProcessingState(false); 
                } else if (status.status === 'cancelled') {
                    console.log('startStatusPolling: Task reported as cancelled.');
                    this.stopPolling('status');
                    this.showStatusMessage('Task cancelled.', 'info');
                    this.setProcessingState(false);
                    this.hideQueueInfo();
                    this.elements.queueControls.style.display = 'none';
                }
            } catch (error) {
                console.error('startStatusPolling: Error during status polling:', error);
                this.handleError(error, 'Analysis status check failed');
                this.stopPolling('status');
            }
        }, 1500);
    }
    
    /**
     * Updates and displays queue information (position and total size).
     * @param {number} position - The user's position in the queue (1-based).
     * @param {number} totalSize - The total number of items in the queue.
     */
    updateQueueInfo(position, totalSize) {
        console.log(`Function: updateQueueInfo called. Position: ${position}, Total: ${totalSize}`);
        if (position !== -1 && totalSize > 0) {
            this.elements.queueInfo.textContent = `Queue: ${totalSize} pending tasks. Your position: ${position}`;
            this.elements.queueInfo.className = 'status-message info';
            this.elements.queueInfo.style.display = 'block';
        } else if (totalSize > 0) {
            this.elements.queueInfo.textContent = `Queue: ${totalSize} pending tasks.`;
            this.elements.queueInfo.className = 'status-message info';
            this.elements.queueInfo.style.display = 'block';
        } else {
            this.hideQueueInfo();
        }
    }

    /** Hides the queue information display. */
    hideQueueInfo() {
        this.elements.queueInfo.style.display = 'none';
        this.elements.queueInfo.textContent = '';
        console.log('Function: hideQueueInfo called. Queue info hidden.');
    }

    /**
     * Handles an action request for the current task in the queue.
     * @param {'cancel'} actionType - The type of queue action.
     */
    async handleQueueAction(actionType) {
        console.log(`Function: handleQueueAction called for action: ${actionType}`);
        // This check ensures action is only performed if there's a session and it's in a cancellable state.
        if (!this.currentSessionId || (!this.isProcessing && this.elements.queueControls.style.display === 'none')) { 
            console.warn('handleQueueAction: No active session or controls not visible, returning.');
            return;
        }

        const isConfirmed = await this.showConfirmModal(
            'Confirm Cancellation',
            'Are you sure you want to stop this task? Press "Stop" to halt the process, or "Continue" to let it finish.'
        );

        if (!isConfirmed) { // isConfirmed is true if 'Stop' was clicked, false if 'Continue' was clicked
            console.log('handleQueueAction: User chose to continue.');
            return; // If user chose to continue, do nothing further.
        }

        // If code reaches here, user chose to "Stop"
        try {
            this.showStatusMessage(`Sending ${actionType} request...`, 'info');
            console.log(`handleQueueAction: Sending request to /api/queue/${actionType}`);
            const endpoint = `/api/queue/${actionType}`;
            const response = await fetch(endpoint, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ session_id: this.currentSessionId })
            });

            const responseText = await response.text();
            console.log('handleQueueAction: Received response (raw text):', responseText);
            if (!response.ok) {
                console.error('handleQueueAction: API request failed with status:', response.status, response.statusText, responseText);
                throw new Error(responseText || `Failed to ${actionType} task`);
            }

            const result = JSON.parse(responseText);
            this.showStatusMessage(result.message, 'success', 3000);
            console.log('handleQueueAction: API request successful, result:', result);
            
            this.startStatusPolling(); 

        } catch (error) {
            console.error('handleQueueAction: Error in try-catch block:', error);
            this.handleError(error, `Failed to ${actionType} task`);
        }
    }

    /**
     * Processes metadata upon successful bundle analysis completion.
     * Displays results to the user.
     * @param {object} metadata - The analysis metadata received from the server.
     */
    handleAnalysisComplete(metadata) {
        console.log('Function: handleAnalysisComplete called.');
        this.bundleMetadata = metadata;
        this.setProcessingState(false);
        this.displayResults(metadata);
        this.showStatusMessage('Analysis complete!', 'success', 3000);
        this.hideErrorCard(); 
        this.hideQueueInfo();
        this.elements.queueControls.style.display = 'none';
        console.log('handleAnalysisComplete: Analysis completed, results displayed.');
    }
    
    /**
     * Renders the analysis results, including bundle info, asset classes, and the asset list.
     * @param {object} metadata - The analysis metadata.
     */
    displayResults(metadata) {
        console.log('Function: displayResults called with metadata:', metadata);
        if (!metadata || !metadata.bundle_info || !metadata.assets || !metadata.asset_classes) {
            console.error("displayResults: Invalid or incomplete metadata received.", metadata);
            this.displayErrorCard("Analysis completed, but received incomplete or invalid metadata. Cannot display results. This might be due to a server error or a corrupted bundle file.");
            this.setProcessingState(false); 
            return;
        }

        this.elements.metadataInfo.innerHTML = `
            <div><strong>Filename:</strong><br>${this.escapeHtml(metadata.bundle_info.filename || 'N/A')}</div>
            <div><strong>File Size:</strong><br>${this.formatSize(metadata.bundle_info.size)}</div>
            <div><strong>Unity Version:</strong><br>${this.escapeHtml(metadata.bundle_info.unity_version)}</div>
            <div><strong>Platform:</strong><br>${this.escapeHtml(metadata.bundle_info.platform)}</div>
            <div><strong>Objects:</strong><br>${metadata.bundle_info.object_count}</div>
            <div><strong>Compression:</strong><br>${this.escapeHtml(metadata.bundle_info.compression)}</div>
        `;
        this.displayAssetClasses(metadata.asset_classes); 
        this.displayAssetList(metadata.assets);
        this.showResults();
        this.selectedAssets.clear();
        this.updateExtractButton();
        console.log('displayResults: Results displayed on UI.');
    }

    /**
     * Displays the list of unique asset classes found in the bundle.
     * @param {string[]} classes - An array of asset class names.
     */
    displayAssetClasses(classes) {
        console.log('Function: displayAssetClasses called.');
        const container = this.elements.assetClassesList;
        if (!classes || classes.length === 0) {
            this.elements.assetClassesCard.style.display = 'none';
            console.log('displayAssetClasses: No classes, hiding card.');
            return;
        }
        this.elements.assetClassesCard.style.display = 'block';
        
        const classListHtml = classes.map(c => `<li>${this.escapeHtml(c)}</li>`).join('');
        container.innerHTML = `<ul class="class-list">${classListHtml}</ul>`;
        console.log('displayAssetClasses: Asset classes displayed.');
    }
    
    /**
     * Renders the hierarchical list of assets from the bundle.
     * Assets are grouped by category (type) and sorted.
     * @param {object} assets - An object where keys are asset categories and values are arrays of asset data.
     */
    displayAssetList(assets) {
        console.log('Function: displayAssetList called.');
        const container = this.elements.assetListContainer;
        const fragment = document.createDocumentFragment();
        const allAssets = [];
        for (const categoryName in assets) {
            allAssets.push(...assets[categoryName]);
        }

        // Sort assets by type then by name
        allAssets.sort((a, b) => {
            const typeCompare = a.type.localeCompare(b.type);
            if (typeCompare !== 0) return typeCompare;
            return a.name.localeCompare(b.name);
        });

        // Group assets by type for categorized display
        const groupedAssets = allAssets.reduce((acc, asset) => {
            acc[asset.type] = acc[asset.type] || [];
            acc[asset.type].push(asset);
            return acc;
        }, {});

        // Sort categories by number of assets (descending)
        const sortedCategories = Object.entries(groupedAssets).sort(([, a], [, b]) => b.length - a.length);
        
        sortedCategories.forEach(([categoryName, categoryAssets]) => {
            fragment.appendChild(this.createAssetCategory(categoryName, categoryAssets));
        });
        
        container.innerHTML = ''; // Clear previous list
        container.appendChild(fragment);
        
        this.updateExtractButton();
        console.log('displayAssetList: Asset list rendered.');
    }
    
    /**
     * Creates a <details> element representing an asset category.
     * @param {string} name - The name of the asset category.
     * @param {object[]} assets - An array of assets belonging to this category.
     * @returns {HTMLDetailsElement} The created details element.
     */
    createAssetCategory(name, assets) {
        const details = document.createElement('details');
        details.className = 'asset-category';
        details.open = assets.length <= 50; 
        
        const summary = document.createElement('summary');
        summary.innerHTML = `<span class="category-name">${this.escapeHtml(name)} (${assets.length})</span>
                             <input type="checkbox" class="category-checkbox" data-category="${this.escapeHtml(name)}">`;
        
        const assetList = document.createElement('ul');
        assetList.className = 'asset-list';
        assets.forEach(asset => {
            assetList.appendChild(this.createAssetListItem(asset));
        });
        
        details.append(summary, assetList);
        return details;
    }

    /**
     * Creates an <li> element representing a single asset in the list.
     * @param {object} asset - The asset data object.
     * @returns {HTMLLIElement} The created list item element.
     */
    createAssetListItem(asset) {
        const li = document.createElement('li');
        li.dataset.assetIndex = asset.index;
        li.dataset.assetName = asset.name.toLowerCase();
        li.dataset.assetType = asset.type.toLowerCase();
        
        const checkbox = document.createElement('input');
        checkbox.type = 'checkbox';
        checkbox.className = 'asset-checkbox';
        checkbox.dataset.assetIndex = asset.index; 
        checkbox.checked = this.selectedAssets.has(asset.index); 
        
        li.appendChild(checkbox);
        li.innerHTML += `<span class="asset-name">${this.escapeHtml(asset.name)}</span>
                        <span class="asset-type">${this.escapeHtml(asset.type)}</span>
                        <span class="asset-size">${this.formatSize(asset.estimated_size)}</span>`; 
        
        return li;
    }

    /**
     * Formats a size in bytes into a human-readable string (e.g., 1.5 MB).
     * @param {number} bytes - The size in bytes.
     * @returns {string} The formatted size string.
     */
    formatSize(bytes) {
        if (typeof bytes !== 'number' || bytes < 0) return '0 B';
        if (bytes === 0) return '0 B';
        const k = 1024, i = Math.floor(Math.log(bytes) / Math.log(k));
        return `${parseFloat((bytes / Math.pow(k, i)).toFixed(1))} ${['B', 'KB', 'MB', 'GB'][i]}`;
    }
    
    /**
     * Toggles the selection of all assets within a specific category.
     * @param {string} categoryName - The name of the category.
     * @param {boolean} isSelected - True to select, False to deselect.
     */
    toggleCategorySelection(categoryName, isSelected) {
        console.log(`Function: toggleCategorySelection called for ${categoryName}, selected: ${isSelected}`);
        const assets = this.bundleMetadata.assets[categoryName] || [];
        const indicesToUpdate = assets.map(a => a.index); 

        if (isSelected) {
            indicesToUpdate.forEach(index => this.selectedAssets.add(index));
        } else {
            indicesToUpdate.forEach(index => this.selectedAssets.delete(index));
        }

        requestAnimationFrame(() => {
            indicesToUpdate.forEach(index => {
                const checkbox = this.elements.assetListContainer.querySelector(`input[data-asset-index="${index}"]`);
                if (checkbox) checkbox.checked = isSelected;
            });
            this.updateExtractButton(); 
        });
        this.updateCategoryCheckboxes();
    }

    /**
     * Toggles the selection state of an individual asset.
     * @param {number} assetIndex - The index of the asset.
     * @param {boolean} isSelected - True to select, False to deselect.
     */
    toggleAssetSelection(assetIndex, isSelected) {
        console.log(`Function: toggleAssetSelection called for index ${assetIndex}, selected: ${isSelected}`);
        if (isSelected) this.selectedAssets.add(assetIndex);
        else this.selectedAssets.delete(assetIndex);
        
        this.updateCategoryCheckboxes();
        this.updateExtractButton();
    }
    
    /**
     * Updates the indeterminate state and checked status of category checkboxes
     * based on the selection state of their child assets.
     */
    updateCategoryCheckboxes() {
        console.log('Function: updateCategoryCheckboxes called.');
        if (!this.bundleMetadata) return;
        Object.entries(this.bundleMetadata.assets).forEach(([name, assets]) => {
            const checkbox = document.querySelector(`.category-checkbox[data-category="${name}"]`);
            if (!checkbox) return;
            
            const selectedCount = assets.filter(a => this.selectedAssets.has(a.index)).length; 
            checkbox.checked = selectedCount === assets.length && assets.length > 0;
            checkbox.indeterminate = selectedCount > 0 && selectedCount < assets.length;
        });
    }

    /**
     * Selects all assets in the displayed list.
     */
    selectAllAssets() {
        console.log('Function: selectAllAssets called.');
        if (!this.bundleMetadata || !this.bundleMetadata.assets) {
            return;
        }

        this.selectedAssets.clear();
        for (const categoryName in this.bundleMetadata.assets) {
            this.bundleMetadata.assets[categoryName].forEach(asset => {
                this.selectedAssets.add(asset.index); 
            });
        }

        requestAnimationFrame(() => {
            this.elements.assetListContainer.querySelectorAll('input.asset-checkbox').forEach(cb => {
                cb.checked = true;
            });
            this.elements.assetListContainer.querySelectorAll('input.category-checkbox').forEach(cb => {
                cb.checked = true;
                cb.indeterminate = false;
            });
            this.updateExtractButton();
        });
    }

    /**
     * Deselects all assets in the displayed list.
     */
    deselectAllAssets() {
        console.log('Function: deselectAllAssets called.');
        this.selectedAssets.clear();

        requestAnimationFrame(() => {
            this.elements.assetListContainer.querySelectorAll('input.asset-checkbox').forEach(cb => {
                cb.checked = false;
            });
            this.elements.assetListContainer.querySelectorAll('input.category-checkbox').forEach(cb => {
                cb.checked = false;
                cb.indeterminate = false;
            });
            this.updateExtractButton();
        });
    }

    /**
     * Filters the displayed asset list based on user input in the filter field.
     * Matches asset names and types.
     */
    filterAssets() {
        console.log('Function: filterAssets called.');
        const filterText = this.elements.filterInput.value.toLowerCase().trim();
        requestAnimationFrame(() => {
            document.querySelectorAll('.asset-category').forEach(category => {
                let hasVisibleItems = false;
                category.querySelectorAll('li').forEach(item => {
                    const isVisible = !filterText || 
                                     item.dataset.assetName.includes(filterText) ||
                                     item.dataset.assetType.includes(filterText);
                    item.style.display = isVisible ? '' : 'none';
                    if (isVisible) hasVisibleItems = true;
                });
                // Hide/show category based on its visible children
                category.style.display = hasVisibleItems ? '' : 'none';
                
                const categoryCheckbox = category.querySelector('.category-checkbox');
                if (categoryCheckbox && !hasVisibleItems) {
                    categoryCheckbox.checked = false;
                    categoryCheckbox.indeterminate = false;
                }
            });
        });
    }
    
    /**
     * Updates the text and disabled state of the "Extract Selected" button
     * based on the number of currently selected assets.
     */
    updateExtractButton() {
        console.log('Function: updateExtractButton called.');
        const selectionCount = this.selectedAssets.size;
        this.elements.extractButton.disabled = selectionCount === 0 || this.isProcessing;
        this.elements.extractButton.textContent = selectionCount > 0
            ? `Extract Selected (${selectionCount}) as .ZIP`
            : 'Extract Selected as .ZIP';
    }
    
    /**
     * Handles the initiation of the asset extraction process.
     * Sends a request to the server with selected asset indices.
     */
    async handleAssetExtraction() {
        console.log('Function: handleAssetExtraction called.');
        if (this.selectedAssets.size === 0) {
            const errorMessage = 'Select at least one asset.';
            this.showStatusMessage(errorMessage, 'error');
            this.displayErrorCard(errorMessage);
            console.error('handleAssetExtraction: No assets selected, returning.');
            return;
        }
        
        try {
            this.setProcessingState(true, 'extracting');
            console.log('handleAssetExtraction: Processing state set to extracting.');
            const response = await fetch('/api/extract', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    session_id: this.currentSessionId,
                    selected_assets: Array.from(this.selectedAssets),
                })
            });
            
            const responseText = await response.text();
            console.log('handleAssetExtraction: Received /api/extract response (raw text):', responseText);

            if (!response.ok) {
                console.error('handleAssetExtraction: Extraction request failed with status:', response.status, response.statusText, responseText);
                throw new Error(responseText || 'Extraction request failed');
            }
            
            let result;
            try {
                result = JSON.parse(responseText);
            } catch (jsonError) {
                console.error('handleAssetExtraction: Failed to parse /api/extract response as JSON:', jsonError, responseText);
                throw new Error('Invalid JSON response from server during extraction request: ' + responseText);
            }
            console.log('handleAssetExtraction: Extraction request successful, result:', result);
            this.startExtractionPolling();
            this.hideErrorCard(); 
            
        } catch (error) {
            console.error('handleAssetExtraction: Error in try-catch block:', error);
            this.handleError(error, 'Extraction failed');
        }
    }
    
    /**
     * Starts polling the server for extraction status updates.
     * Updates progress bar and initiates download upon completion.
     */
    startExtractionPolling() {
        this.stopPolling('extraction');
        console.log('Function: startExtractionPolling called for session:', this.currentSessionId);
        this.extractionPollingInterval = setInterval(async () => {
            try {
                console.log('startExtractionPolling: Fetching status for session:', this.currentSessionId);
                const response = await fetch(`/api/extraction-status/${this.currentSessionId}`);
                const responseText = await response.text();
                
                if (!response.ok) {
                    console.error('startExtractionPolling: Extraction status check failed with status:', response.status, response.statusText, responseText);
                    throw new Error(responseText || 'Extraction status check failed');
                }
                
                let status;
                try {
                    status = JSON.parse(responseText);
                } catch (jsonError) {
                    console.error('startExtractionPolling: Failed to parse /api/extraction-status response as JSON:', jsonError, responseText);
                    throw new Error('Invalid JSON response from server during extraction status check: ' + responseText);
                }
                
                console.log('startExtractionPolling: Received extraction status response:', status);
                
                this.updateProgress(status.progress || 0);
                
                if (status.status === 'completed' && status.download_ready) {
                    console.log('startExtractionPolling: Extraction completed successfully, download ready.');
                    this.stopPolling('extraction');
                    this.handleExtractionComplete();
                } else if (status.status === 'error') {
                    console.error('startExtractionPolling: Extraction reported error:', status.error);
                    this.stopPolling('extraction');
                    let errorMessage = status.error || 'Extraction failed on server';
                    if (typeof errorMessage === 'object' && errorMessage.error) {
                        errorMessage = errorMessage.error; 
                    }
                    this.displayErrorCard(errorMessage); 
                    this.setProcessingState(false); 
                }
            } catch (error) {
                console.error('startExtractionPolling: Error during extraction polling:', error);
                this.handleError(error, 'Extraction status check failed');
                this.stopPolling('extraction');
            }
        }, 1500);
    }
    
    /**
     * Handles actions upon successful asset extraction completion.
     * Triggers the download of the resulting ZIP archive.
     */
    handleExtractionComplete() {
        console.log('Function: handleExtractionComplete called.');
        this.setProcessingState(false);
        this.showStatusMessage('Extraction complete! Download starting...', 'success', 5000);
        this.hideErrorCard(); 
        
        const link = document.createElement('a');
        link.href = `/api/download/${this.currentSessionId}`;
        link.download = `unity_assets_${this.currentSessionId}.zip`;
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        console.log('handleExtractionComplete: Download initiated.');
    }

    /**
     * Stops an active polling interval.
     * @param {'status'|'extraction'} type - The type of polling to stop.
     */
    stopPolling(type) {
        if (type === 'status' && this.statusPollingInterval) {
            clearInterval(this.statusPollingInterval);
            this.statusPollingInterval = null;
            console.log(`Function: stopPolling called. Stopped ${type} polling.`);
        } else if (type === 'extraction' && this.extractionPollingInterval) {
            clearInterval(this.extractionPollingInterval);
            this.extractionPollingInterval = null;
            console.log(`Function: stopPolling called. Stopped ${type} polling.`);
        }
    }

    /**
     * Handles and displays errors encountered during application processes.
     * Shows a status message and an error card with details.
     * @param {Error|string} error - The error object or message.
     * @param {string} context - A descriptive context for the error.
     */
    handleError(error, context) {
        console.error(`Function: handleError called. Context: ${context}, Error:`, error);
        let displayMessage = `An unexpected error occurred: ${error.message || error}`;
        try {
            const errorObj = JSON.parse(error.message || String(error));
            if (errorObj && errorObj.error) {
                displayMessage = errorObj.error;
            }
        } catch (e) {
            
        }
        
        this.showStatusMessage(displayMessage, 'error'); 
        this.displayErrorCard(displayMessage); 
        this.setProcessingState(false);
        console.log(`handleError: Error message displayed: ${displayMessage}`);
    }
    
    /**
     * Displays a dedicated error card with a given message.
     * Hides other sections like results and optional upload.
     * @param {string} message - The error message to display.
     */
    displayErrorCard(message) {
        console.log('Function: displayErrorCard called with message:', message);
        this.elements.errorInfoContent.textContent = message;
        this.elements.errorInfoCard.style.display = 'block';
        this.elements.resultsSection.style.display = 'none'; 
        this.elements.optionalUploadSection.style.display = 'none'; 

        // Add specific guidance for .resS file errors if detected in the message
        if (typeof message === 'string' && message.includes("Resource file") && message.includes(".resS not found")) {
            const resSGuidance = document.createElement('p');
            resSGuidance.style.marginTop = '1rem';
            resSGuidance.style.fontSize = '0.9rem';
            resSGuidance.innerHTML = '<strong>Important:</strong> If you see "Resource file ... .resS not found" for a Texture2D, please ensure you upload all accompanying files (e.g., .assets and its .resS counterpart) together in the main upload area.';
            this.elements.errorInfoContent.appendChild(resSGuidance);
            console.log('displayErrorCard: Added .resS guidance.');
        }
    }

    /**
     * Hides the error information card.
     */
    hideErrorCard() {
        this.elements.errorInfoCard.style.display = 'none';
        this.elements.errorInfoContent.textContent = ''; 
        console.log('Function: hideErrorCard called. Error card hidden.');
    }

    /**
     * Sets the overall processing state of the application.
     * Disables/enables buttons, shows/hides progress bar, and updates text.
     * @param {boolean} isProcessing - True if a process is active, False otherwise.
     * @param {string} [state=''] - A descriptive string for the current process (e.g., 'analyzing', 'extracting', 'queued').
     */
    setProcessingState(isProcessing, state = '') {
        console.log(`Function: setProcessingState called. isProcessing: ${isProcessing}, state: ${state}`);
        // `isProcessing` flag is now primarily for the upload button and general UI blocking.
        this.isProcessing = isProcessing; 
        this.elements.uploadButton.disabled = isProcessing;
        
        // Update Extract button based on asset selection AND not being in a final state
        this.elements.extractButton.disabled = this.selectedAssets.size === 0 || isProcessing;
        
        // Control visibility and enabled state of the Cancel button
        if (state === 'queued' || state === 'analyzing' || state === 'extracting') {
            this.elements.cancelQueueButton.disabled = false; // Enable cancel button during these states
            this.elements.queueControls.style.display = 'flex'; // Ensure controls are shown
            console.log('setProcessingState: Queue controls enabled and visible.');
        } else {
            this.elements.cancelQueueButton.disabled = true; // Disable if not in cancellable state
            this.elements.queueControls.style.display = 'none'; // Hide controls when idle or finished
            console.log('setProcessingState: Queue controls disabled and hidden.');
        }


        if (isProcessing) {
            this.elements.uploadButton.textContent = 'Processing...';
            this.showProgressBar();
            this.hideResults();
            this.hideStatusMessage();
            this.hideErrorCard(); 
            // Queue info is handled by updateQueueInfo, don't hide here
            console.log('setProcessingState: Processing state set, UI updated for active processing.');
        } else {
            this.elements.uploadButton.textContent = 'Analyze Bundle';
            this.hideProgressBar();
            this.hideQueueInfo(); // Hide queue info when not processing
            console.log('setProcessingState: Processing state reset, UI updated for idle.');
        }
    }
    
    /** Shows the progress bar. */
    showProgressBar() { this.elements.progressBar.style.display = 'block'; this.updateProgress(0); console.log('Function: showProgressBar called. Progress bar shown.'); }
    /** Hides the progress bar. */
    hideProgressBar() { this.elements.progressBar.style.display = 'none'; console.log('Function: hideProgressBar called. Progress bar hidden.'); }
    /**
     * Updates the width of the progress bar inner element.
     * @param {number} percentage - The percentage of progress (0-100).
     */
    updateProgress(percentage) { this.elements.progressBarInner.style.width = `${Math.max(0, Math.min(100, percentage))}%`; console.log(`Function: updateProgress called. Progress: ${percentage}%`); }
    /** Shows the results section. */
    showResults() { this.elements.resultsSection.style.display = 'block'; console.log('Function: showResults called. Results section shown.'); }
    /** Hides the results section. */
    hideResults() { this.elements.resultsSection.style.display = 'none'; console.log('Function: hideResults called. Results section hidden.'); }
    
    /**
     * Displays a status message to the user.
     * @param {string} message - The message text.
     * @param {'info'|'success'|'error'|'warning'} [type='info'] - The type of message for styling.
     * @param {number} [timeout=0] - Duration in milliseconds after which the message will hide (0 for no auto-hide).
     */
    showStatusMessage(message, type = 'info', timeout = 0) {
        const el = this.elements.statusMessage;
        el.textContent = message;
        el.className = `status-message ${type}`;
        el.style.display = 'block';
        if (timeout > 0) setTimeout(() => this.hideStatusMessage(), timeout);
        console.log(`Function: showStatusMessage called. Message: "${message}" (Type: ${type})`);
    }
    
    /** Hides the status message. */
    hideStatusMessage() { this.elements.statusMessage.style.display = 'none'; console.log('Function: hideStatusMessage called. Status message hidden.'); }
    
    /**
     * Escapes HTML characters in a given text string to prevent XSS.
     * @param {string} text - The text to escape.
     * @returns {string} The HTML-escaped string.
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Initialize the application once the DOM is fully loaded.
document.addEventListener('DOMContentLoaded', () => new UnityBundleExtractor());

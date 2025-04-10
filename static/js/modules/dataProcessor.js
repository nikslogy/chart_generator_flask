/**
 * Data Processor module - Handles sheet data loading and processing
 */

export const DataProcessor = {
    // State variables
    currentFileName: '',
    currentSheetName: '',
    sheetData: [],
    columns: [],
    
    // Load sheet data from selected sheet
    loadSheetData: function(filename, sheetName, callbacks) {
        // Store the filename and sheet name in the module state
        this.currentFileName = filename;
        this.currentSheetName = sheetName;
        
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        
        // Log what we're sending for debugging
        console.log('Sending request with:', {
            filename: this.currentFileName,
            sheet: this.currentSheetName
        });
        
        fetch('/get_sheet_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                filename: this.currentFileName,
                sheet: this.currentSheetName
            })
        })
        .then(response => {
            // Log the raw response for debugging
            console.log('Response status:', response.status);
            return response.json();
        })
        .then(data => {
            loadingIndicator.classList.add('hidden');
            console.log('Response data:', data);
            
            if (data.success) {
                this.columns = data.columns;
                this.sheetData = data.data;
                
                if (callbacks && callbacks.onDataLoaded) {
                    callbacks.onDataLoaded(data.columns, data.data, data.rowCount);
                }
            } else {
                alert('Error: ' + data.error);
                console.error('Server error:', data.error);
            }
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error loading sheet data:', error);
            alert('Error loading sheet data. Please try again.');
        });
    },
    
    // Apply filters to data
    applyFilters: function(filterOptions, callbacks) {
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        
        // Ensure we're sending the current filename and sheet name
        const requestData = {
            filename: this.currentFileName,
            sheet: this.currentSheetName,
            ...filterOptions
        };
        
        console.log('Applying filters with:', requestData);
        
        fetch('/filter_data', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('hidden');
            
            if (data.success) {
                if (callbacks && callbacks.onFilterApplied) {
                    callbacks.onFilterApplied(data.data, data.uniqueValues);
                }
            } else {
                alert('Error: ' + data.error);
                console.error('Filter error:', data.error);
            }
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error applying filters:', error);
            alert('Error applying filters. Please try again.');
        });
    },
    
    // Get column unique values for filtering
    getColumnUniqueValues: function(data, column) {
        if (!data || !column) return [];
        
        const values = new Set();
        
        data.forEach(row => {
            if (row[column] !== null && row[column] !== undefined) {
                values.add(row[column]);
            }
        });
        
        return Array.from(values).sort();
    }
}; 
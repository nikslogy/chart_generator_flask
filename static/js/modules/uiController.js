/**
 * UI Controller module - Handles UI updates and interactions
 */

export const UIController = {
    // Update column selectors with available columns
    populateColumnSelectors: function(columns) {
        const xAxisSelect = document.getElementById('xAxisSelect');
        const yAxisSelects = document.querySelectorAll('.y-axis-select');
        const filterColumnSelect = document.getElementById('filterColumn');
        const filterColumn2Select = document.getElementById('filterColumn2');
        
        // Clear existing options
        xAxisSelect.innerHTML = '';
        filterColumnSelect.innerHTML = '<option value="">No Filter</option>';
        filterColumn2Select.innerHTML = '<option value="">No Chart Filter</option>';
        
        yAxisSelects.forEach(select => {
            select.innerHTML = '';
        });
        
        // Add column options
        columns.forEach(column => {
            // X-axis select
            const xOption = document.createElement('option');
            xOption.value = column;
            xOption.textContent = column;
            xAxisSelect.appendChild(xOption);
            
            // Y-axis selects
            yAxisSelects.forEach(select => {
                const yOption = document.createElement('option');
                yOption.value = column;
                yOption.textContent = column;
                select.appendChild(yOption);
            });
            
            // Filter selects
            const filterOption = document.createElement('option');
            filterOption.value = column;
            filterOption.textContent = column;
            filterColumnSelect.appendChild(filterOption);
            
            const filter2Option = document.createElement('option');
            filter2Option.value = column;
            filter2Option.textContent = column;
            filterColumn2Select.appendChild(filter2Option);
        });
    },
    
    // Update preview boxes with selected column values
    updateColumnPreviews: function(data, xAxis, yAxes) {
        const xAxisPreview = document.getElementById('xAxisPreview');
        const yAxisPreview = document.getElementById('yAxisPreview');
        
        // Clear existing previews
        xAxisPreview.innerHTML = '';
        yAxisPreview.innerHTML = '';
        
        if (!data || !data.length) return;
        
        // Get unique x-axis values (limited to first 10)
        const xValues = this.getUniqueValues(data, xAxis).slice(0, 10);
        
        // Show x-axis preview
        xValues.forEach(value => {
            const valueElement = document.createElement('span');
            valueElement.className = 'preview-value';
            valueElement.textContent = value;
            xAxisPreview.appendChild(valueElement);
        });
        
        // Show y-axis preview for first dataset
        if (yAxes && yAxes.length > 0) {
            const yAxis = yAxes[0].column;
            const yColor = yAxes[0].color;
            
            // Get first 5 rows
            const previewRows = data.slice(0, 5);
            
            previewRows.forEach(row => {
                if (row[yAxis] !== null && row[yAxis] !== undefined) {
                    const valueElement = document.createElement('span');
                    valueElement.className = 'preview-value';
                    valueElement.style.backgroundColor = yColor + '30';
                    valueElement.style.borderColor = yColor;
                    valueElement.textContent = row[yAxis];
                    yAxisPreview.appendChild(valueElement);
                }
            });
        }
    },
    
    // Populate filter values dropdown
    populateFilterValues: function(column, data) {
        const filterValueSelect = document.getElementById('filterValue');
        
        // Clear existing options
        filterValueSelect.innerHTML = '';
        
        if (!column) {
            filterValueSelect.disabled = true;
            filterValueSelect.innerHTML = '<option value="">Select column first</option>';
            return;
        }
        
        filterValueSelect.disabled = false;
        
        // Get unique values for the selected column
        const uniqueValues = this.getUniqueValues(data, column);
        
        // Add options
        uniqueValues.forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            filterValueSelect.appendChild(option);
        });
    },
    
    // Populate chart filter values dropdown
    populateChartFilterValues: function(values) {
        const chartFilterValue = document.getElementById('chartFilterValue');
        const chartFilterLabel = document.getElementById('chartFilterLabel');
        
        // Clear existing options
        chartFilterValue.innerHTML = '<option value="">All Values</option>';
        
        // Hide if no values
        if (!values || !values.length) {
            chartFilterValue.parentElement.parentElement.classList.add('hidden');
            return;
        }
        
        // Show the filter controls
        chartFilterValue.parentElement.parentElement.classList.remove('hidden');
        
        // Update filter label
        if (chartFilterLabel) {
            const filterColumn = document.getElementById('filterColumn2').value;
            chartFilterLabel.textContent = `Filter by ${filterColumn}:`;
        }
        
        // Add options
        values.forEach(value => {
            const option = document.createElement('option');
            option.value = value;
            option.textContent = value;
            chartFilterValue.appendChild(option);
        });
    },
    
    // Get random color for chart datasets
    getRandomColor: function() {
        const letters = '0123456789ABCDEF';
        let color = '#';
        for (let i = 0; i < 6; i++) {
            color += letters[Math.floor(Math.random() * 16)];
        }
        return color;
    },
    
    // Get unique values from data for a column
    getUniqueValues: function(data, column) {
        if (!data || !column) return [];
        
        const values = new Set();
        
        data.forEach(row => {
            if (row[column] !== null && row[column] !== undefined) {
                values.add(row[column]);
            }
        });
        
        return Array.from(values).sort();
    },
    
    // Add a new Y-axis series selector
    addYAxisSelector: function(columns) {
        const container = document.getElementById('yAxisSelectors');
        const randomColor = this.getRandomColor();
        
        // Create new y-axis item
        const yAxisItem = document.createElement('div');
        yAxisItem.className = 'y-axis-item';
        
        // Create select
        const select = document.createElement('select');
        select.className = 'y-axis-select';
        
        // Add column options
        columns.forEach(column => {
            const option = document.createElement('option');
            option.value = column;
            option.textContent = column;
            select.appendChild(option);
        });
        
        // Create color picker
        const colorPicker = document.createElement('input');
        colorPicker.type = 'color';
        colorPicker.className = 'series-color';
        colorPicker.value = randomColor;
        
        // Create remove button
        const removeBtn = document.createElement('button');
        removeBtn.className = 'remove-y-axis';
        removeBtn.title = 'Remove series';
        removeBtn.textContent = '✕';
        
        // Add event listener to remove button
        removeBtn.addEventListener('click', function() {
            container.removeChild(yAxisItem);
        });
        
        // Add elements to item
        yAxisItem.appendChild(select);
        yAxisItem.appendChild(colorPicker);
        yAxisItem.appendChild(removeBtn);
        
        // Add item to container
        container.appendChild(yAxisItem);
        
        return select;
    }
}; 
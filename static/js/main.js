/**
 * Main application script that uses all the modules
 */

import { initFileUpload } from './modules/fileUpload.js';
import { DataProcessor } from './modules/dataProcessor.js';
import { ChartGenerator, formatIndianNumber } from './modules/chartGenerator.js';
import { UIController } from './modules/uiController.js';

document.addEventListener('DOMContentLoaded', function() {
    // DOM Elements
    const dataSelection = document.getElementById('data-selection');
    const sheetSelect = document.getElementById('sheetSelect');
    const xAxisSelect = document.getElementById('xAxisSelect');
    const yAxisSelectors = document.getElementById('yAxisSelectors');
    const chartTypeSelection = document.getElementById('chart-type-selection');
    const chartDisplay = document.getElementById('chart-display');
    const chartCanvas = document.getElementById('chartCanvas');
    const startRowInput = document.getElementById('startRow');
    const endRowInput = document.getElementById('endRow');
    const applyRangeBtn = document.getElementById('applyRange');
    const generateChartBtn = document.getElementById('generateChartBtn');
    const filterColumnSelect = document.getElementById('filterColumn');
    const filterValueSelect = document.getElementById('filterValue');
    const filterColumn2Select = document.getElementById('filterColumn2');
    const chartFilterValue = document.getElementById('chartFilterValue');
    const chartTitleInput = document.getElementById('chartTitle');
    const xAxisLabelInput = document.getElementById('xAxisLabel');
    const yAxisLabelInput = document.getElementById('yAxisLabel');
    const applyChartTitleBtn = document.getElementById('applyChartTitle');
    const applyAxisLabelsBtn = document.getElementById('applyAxisLabels');
    const downloadImageBtn = document.getElementById('downloadImageBtn');
    const downloadCodeBtn = document.getElementById('downloadCodeBtn');
    const copyDataBtn = document.getElementById('copyDataBtn');
    const yMinValueInput = document.getElementById('yMinValue');
    const yMaxValueInput = document.getElementById('yMaxValue');
    const applyYAxisRangeBtn = document.getElementById('applyYAxisRange');
    const resetYAxisRangeBtn = document.getElementById('resetYAxisRange');
    const chartDescription = document.getElementById('chartDescription');
    const chartAdditionalInfo = document.getElementById('chartAdditionalInfo');
    const shareChartBtn = document.getElementById('shareChartBtn');
    const downloadChartWithInfoBtn = document.getElementById('downloadChartWithInfoBtn');
    const addSeriesBtn = document.getElementById('addSeries');
    
    // State variables
    let selectedChartType = '';
    
    // Initialize file upload handling
    initFileUpload({
        onUploadSuccess: function(filename, sheets) {
            console.log('File upload success callback with filename:', filename);
            DataProcessor.currentFileName = filename; // Ensure filename is set here

            // Populate sheet select
            populateSheetSelect(sheets);
            
            // Show data selection section
            dataSelection.classList.remove('hidden');
        }
    });
    
    // Populate sheet selector dropdown
    function populateSheetSelect(sheets) {
        sheetSelect.innerHTML = '';
        
        sheets.forEach(sheet => {
            const option = document.createElement('option');
            option.value = sheet;
            option.textContent = sheet;
            sheetSelect.appendChild(option);
        });
        
        // Trigger sheet selection to load first sheet
        sheetSelect.dispatchEvent(new Event('change'));
    }
    
    // Handle sheet selection
    sheetSelect.addEventListener('change', function() {
        console.log('Sheet selected:', this.value);
        console.log('Current filename:', DataProcessor.currentFileName);
        
        // Double check we have a filename
        if (!DataProcessor.currentFileName) {
            // Try to restore from localStorage
            DataProcessor.currentFileName = localStorage.getItem('currentFileName');
            console.log('Restored filename from localStorage:', DataProcessor.currentFileName);
            
            if (!DataProcessor.currentFileName) {
                alert('Error: No file selected. Please upload a file first.');
                return;
            }
        }
        
        DataProcessor.loadSheetData(DataProcessor.currentFileName, this.value, {
            onDataLoaded: function(columns, data, rowCount) {
                // Update row count
                endRowInput.value = rowCount + 1; // +1 for header row
                
                // Populate column selectors
                UIController.populateColumnSelectors(columns);
                
                // Show chart type selection
                chartTypeSelection.classList.remove('hidden');
            }
        });
    });
    
    // Handle X-axis selection
    xAxisSelect.addEventListener('change', updateXAxisPreview);
    
    function updateXAxisPreview() {
        const xAxis = xAxisSelect.value;
        const yAxes = getSelectedYAxes();
        
        UIController.updateColumnPreviews(DataProcessor.sheetData, xAxis, yAxes);
    }
    
    // Handle Y-axis selection
    document.addEventListener('change', function(e) {
        if (e.target.classList.contains('y-axis-select') || e.target.classList.contains('series-color')) {
            updateYAxisPreview();
        }
    });
    
    function updateYAxisPreview() {
        const xAxis = xAxisSelect.value;
        const yAxes = getSelectedYAxes();
        
        UIController.updateColumnPreviews(DataProcessor.sheetData, xAxis, yAxes);
    }
    
    // Add Y-axis series
    addSeriesBtn.addEventListener('click', function() {
        UIController.addYAxisSelector(DataProcessor.columns);
    });
    
    // Remove Y-axis series
    yAxisSelectors.addEventListener('click', function(e) {
        if (e.target.classList.contains('remove-y-axis')) {
            const item = e.target.parentElement;
            yAxisSelectors.removeChild(item);
            updateYAxisPreview();
        }
    });
    
    // Handle filter column selection
    filterColumnSelect.addEventListener('change', function() {
        UIController.populateFilterValues(this.value, DataProcessor.sheetData);
    });
    
    // Apply data range and filters
    applyRangeBtn.addEventListener('click', applyFilters);
    
    function applyFilters() {
        const filterOptions = {
            startRow: parseInt(startRowInput.value, 10) || 1,
            endRow: parseInt(endRowInput.value, 10) || null,
            filterColumn: filterColumnSelect.value,
            filterValue: filterValueSelect.value
        };
        
        DataProcessor.applyFilters(filterOptions, {
            onFilterApplied: function(data) {
                // Update previews with filtered data
                const xAxis = xAxisSelect.value;
                const yAxes = getSelectedYAxes();
                UIController.updateColumnPreviews(data, xAxis, yAxes);
            }
        });
    }
    
    // Chart type selection
    document.querySelectorAll('.chart-type-card').forEach(card => {
        card.addEventListener('click', function() {
            // Remove active class from all cards
            document.querySelectorAll('.chart-type-card').forEach(c => {
                c.classList.remove('active');
            });
            
            // Add active class to clicked card
            this.classList.add('active');
            
            // Store selected chart type
            selectedChartType = this.dataset.type;
        });
    });
    
    // Generate chart
    generateChartBtn.addEventListener('click', function() {
        if (!selectedChartType) {
            alert('Please select a chart type');
            return;
        }
        
        const xAxis = xAxisSelect.value;
        const yAxes = getSelectedYAxes();
        
        if (!xAxis || yAxes.length === 0) {
            alert('Please select X-axis and at least one Y-axis column');
            return;
        }
        
        // Double check we have a filename
        if (!DataProcessor.currentFileName) {
            // Try to restore from localStorage
            DataProcessor.currentFileName = localStorage.getItem('currentFileName');
            
            if (!DataProcessor.currentFileName) {
                alert('Error: No file selected. Please upload a file first.');
                return;
            }
        }
        
        // Double check we have a sheet name
        if (!DataProcessor.currentSheetName) {
            DataProcessor.currentSheetName = sheetSelect.value;
        }
        
        console.log('Generating chart with:', {
            filename: DataProcessor.currentFileName,
            sheet: DataProcessor.currentSheetName,
            chartType: selectedChartType
        });
        
        const chartOptions = {
            filename: DataProcessor.currentFileName,
            sheet: DataProcessor.currentSheetName,
            xAxis: xAxis,
            yAxes: yAxes,
            chartType: selectedChartType,
            startRow: parseInt(startRowInput.value, 10) || 1,
            endRow: parseInt(endRowInput.value, 10) || null,
            filterColumn: filterColumnSelect.value,
            filterValue: filterValueSelect.value,
            chartFilterColumn: filterColumn2Select.value
        };
        
        ChartGenerator.generateChart(chartOptions, {
            onChartGenerated: function(chartData, chartType, filterValues) {
                // Show chart display section
                chartDisplay.classList.remove('hidden');
                
                // Create chart
                ChartGenerator.createChart(chartCanvas, chartData, chartType);
                
                // Populate chart filter dropdown if available
                UIController.populateChartFilterValues(filterValues);
                
                // Scroll to chart
                chartDisplay.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }
        });
    });
    
    // Apply chart filter
    chartFilterValue.addEventListener('change', function() {
        const filterOptions = {
            filename: DataProcessor.currentFileName,
            sheet: DataProcessor.currentSheetName,
            xAxis: xAxisSelect.value,
            yAxes: getSelectedYAxes(),
            chartType: selectedChartType,
            startRow: parseInt(startRowInput.value, 10) || 1,
            endRow: parseInt(endRowInput.value, 10) || null,
            filterColumn: filterColumnSelect.value,
            filterValue: filterValueSelect.value,
            chartFilterColumn: filterColumn2Select.value,
            chartFilterValue: this.value,
            visibleDatasets: getVisibleDatasets()
        };
        
        ChartGenerator.applyChartFilter(filterOptions, {
            onFilterApplied: function(chartData) {
                ChartGenerator.updateChart(chartData);
            }
        });
    });
    
    // Apply chart title
    applyChartTitleBtn.addEventListener('click', function() {
        if (!ChartGenerator.currentChart) return;
        
        const title = chartTitleInput.value;
        
        if (title) {
            ChartGenerator.chartOptions.plugins.title = {
                display: true,
                text: title,
                font: {
                    size: 18,
                    weight: 'bold'
                },
                padding: {
                    top: 10,
                    bottom: 20
                }
            };
        } else {
            ChartGenerator.chartOptions.plugins.title = {
                display: false
            };
        }
        
        ChartGenerator.currentChart.options = ChartGenerator.chartOptions;
        ChartGenerator.currentChart.update();
    });
    
    // Apply axis labels
    applyAxisLabelsBtn.addEventListener('click', function() {
        if (!ChartGenerator.currentChart) return;
        
        const xLabel = xAxisLabelInput.value;
        const yLabel = yAxisLabelInput.value;
        
        ChartGenerator.chartOptions.scales = ChartGenerator.chartOptions.scales || {};
        ChartGenerator.chartOptions.scales.x = ChartGenerator.chartOptions.scales.x || {};
        ChartGenerator.chartOptions.scales.y = ChartGenerator.chartOptions.scales.y || {};
        
        if (xLabel) {
            ChartGenerator.chartOptions.scales.x.title = {
                display: true,
                text: xLabel,
                font: {
                    size: 14,
                    weight: 'bold'
                },
                padding: {
                    top: 10
                }
            };
        } else {
            ChartGenerator.chartOptions.scales.x.title = {
                display: false
            };
        }
        
        if (yLabel) {
            ChartGenerator.chartOptions.scales.y.title = {
                display: true,
                text: yLabel,
                font: {
                    size: 14,
                    weight: 'bold'
                },
                padding: {
                    right: 10
                }
            };
        } else {
            ChartGenerator.chartOptions.scales.y.title = {
                display: false
            };
        }
        
        ChartGenerator.currentChart.options = ChartGenerator.chartOptions;
        ChartGenerator.currentChart.update();
    });
    
    // Apply Y-axis range
    applyYAxisRangeBtn.addEventListener('click', function() {
        if (!ChartGenerator.currentChart) return;
        
        const min = yMinValueInput.value ? parseFloat(yMinValueInput.value) : undefined;
        const max = yMaxValueInput.value ? parseFloat(yMaxValueInput.value) : undefined;
        
        ChartGenerator.chartOptions.scales = ChartGenerator.chartOptions.scales || {};
        ChartGenerator.chartOptions.scales.y = ChartGenerator.chartOptions.scales.y || {};
        
        ChartGenerator.chartOptions.scales.y.min = min;
        ChartGenerator.chartOptions.scales.y.max = max;
        
        ChartGenerator.currentChart.options = ChartGenerator.chartOptions;
        ChartGenerator.currentChart.update();
    });
    
    // Reset Y-axis range
    resetYAxisRangeBtn.addEventListener('click', function() {
        if (!ChartGenerator.currentChart) return;
        
        yMinValueInput.value = '';
        yMaxValueInput.value = '';
        
        ChartGenerator.chartOptions.scales = ChartGenerator.chartOptions.scales || {};
        ChartGenerator.chartOptions.scales.y = ChartGenerator.chartOptions.scales.y || {};
        
        delete ChartGenerator.chartOptions.scales.y.min;
        delete ChartGenerator.chartOptions.scales.y.max;
        
        ChartGenerator.currentChart.options = ChartGenerator.chartOptions;
        ChartGenerator.currentChart.update();
    });
    
    // Download chart as image
    downloadImageBtn.addEventListener('click', function() {
        const title = chartTitleInput.value || 'chart';
        ChartGenerator.downloadChartImage(chartCanvas, title);
    });
    
    // Download chart HTML code
    downloadCodeBtn.addEventListener('click', function() {
        // Include all necessary parameters for filtering
        const options = {
            // Chart metadata
            chartTitle: chartTitleInput.value || 'Excel Data Chart',
            chartDescription: chartDescription.value || '',
            chartAdditionalInfo: chartAdditionalInfo.value || '',
            
            // Chart filter parameters
            chartFilterColumn: filterColumn2Select.value,
            chartFilterValues: Array.from(chartFilterValue.options).slice(1).map(opt => opt.value),
            chartFilterValue: chartFilterValue.value,
            visibleDatasets: getVisibleDatasets(),
            
            // Data source parameters required for full filter data generation
            filename: DataProcessor.currentFileName,
            sheet: DataProcessor.currentSheetName,
            xAxis: xAxisSelect.value,
            yAxes: getSelectedYAxes(),
            filterColumn: filterColumnSelect.value,
            filterValue: filterValueSelect.value,
            startRow: parseInt(startRowInput.value, 10) || 1,
            endRow: parseInt(endRowInput.value, 10) || null
        };
        
        console.log('Downloading chart code with options:', options);
        
        // Call the chart generator to download the code
        ChartGenerator.downloadChartCode(options);
    });
    
    // Copy chart data to clipboard
    copyDataBtn.addEventListener('click', function() {
        if (!ChartGenerator.chartData) return;
        
        const dataStr = JSON.stringify(ChartGenerator.chartData, null, 2);
        navigator.clipboard.writeText(dataStr)
            .then(() => alert('Chart data copied to clipboard!'))
            .catch(err => console.error('Failed to copy:', err));
    });
    
    // Helper function to get selected Y-axis columns and their colors
    function getSelectedYAxes() {
        const yAxes = [];
        const yAxisSelects = document.querySelectorAll('.y-axis-select');
        const seriesColors = document.querySelectorAll('.series-color');
        
        yAxisSelects.forEach((select, index) => {
            if (select.value) {
                yAxes.push({
                    column: select.value,
                    color: seriesColors[index].value || '#4e73df'
                });
            }
        });
        
        return yAxes;
    }
    
    // Helper function to get indices of visible datasets
    function getVisibleDatasets() {
        if (!ChartGenerator.currentChart) return [];
        
        const visibleDatasets = [];
        ChartGenerator.currentChart.data.datasets.forEach((dataset, index) => {
            if (!ChartGenerator.currentChart.getDatasetMeta(index).hidden) {
                visibleDatasets.push(index);
            }
        });
        
        return visibleDatasets;
    }
}); 
/**
 * Chart Generator module - Handles chart creation and management
 */

// Initialize Chart.js plugins
if (typeof window !== 'undefined' && window.Chart) {
    // For Chart.js v2 compatibility
    if (window['chartjs-plugin-datalabels']) {
        Chart.plugins.register(window['chartjs-plugin-datalabels']);
    }
}

export const ChartGenerator = {
    // State variables
    currentChart: null,
    selectedChartType: '',
    chartData: null,
    chartOptions: {},
    originalData: null,
    
    // Generate a new chart
    generateChart: function(chartOptions, callbacks) {
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        
        fetch('/generate_chart', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(chartOptions)
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('hidden');
            
            if (data.success) {
                this.chartData = data.chartData;
                this.originalData = JSON.parse(JSON.stringify(data.chartData)); // Deep copy
                this.selectedChartType = data.chartType;
                
                // Convert data to percentages for stacked percentage bar charts
                if (this.selectedChartType === 'percentStackedBar') {
                    // Store original values before percentages
                    this.chartData.datasets.forEach(dataset => {
                        dataset.originalData = [...dataset.data];
                    });
                    
                    // Calculate column totals
                    const totals = Array(this.chartData.labels.length).fill(0);
                    this.chartData.datasets.forEach(dataset => {
                        dataset.data.forEach((value, index) => {
                            // Only add value to total if it's not null
                            if (value !== null && value !== undefined) {
                                totals[index] += Number(value) || 0;
                            }
                        });
                    });
                    
                    // Convert each value to percentage
                    this.chartData.datasets.forEach(dataset => {
                        dataset.data = dataset.data.map((value, index) => {
                            // Preserve null values
                            if (value === null || value === undefined) {
                                return null;
                            }
                            return totals[index] > 0 ? ((Number(value) || 0) / totals[index]) * 100 : 0;
                        });
                    });
                }
                
                if (callbacks && callbacks.onChartGenerated) {
                    callbacks.onChartGenerated(
                        data.chartData, 
                        data.chartType, 
                        data.chartFilterValues
                    );
                }
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error:', error);
            alert('Error generating chart. Please try again.');
        });
    },
    
    // Apply chart filter
    applyChartFilter: function(filterOptions, callbacks) {
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        
        fetch('/apply_chart_filter', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(filterOptions)
        })
        .then(response => response.json())
        .then(data => {
            loadingIndicator.classList.add('hidden');
            
            if (data.success) {
                this.chartData = data.chartData;
                
                // Convert to percentages for stacked percentage bar charts
                if (this.selectedChartType === 'percentStackedBar') {
                    // Store original values first
                    this.chartData.datasets.forEach(dataset => {
                        dataset.originalData = [...dataset.data];
                    });
                    
                    // Calculate column totals
                    const totals = Array(this.chartData.labels.length).fill(0);
                    this.chartData.datasets.forEach(dataset => {
                        dataset.data.forEach((value, index) => {
                            // Only add value to total if it's not null
                            if (value !== null && value !== undefined) {
                                totals[index] += Number(value) || 0;
                            }
                        });
                    });
                    
                    // Convert each value to percentage
                    this.chartData.datasets.forEach(dataset => {
                        dataset.data = dataset.data.map((value, index) => {
                            // Preserve null values
                            if (value === null || value === undefined) {
                                return null;
                            }
                            return totals[index] > 0 ? ((Number(value) || 0) / totals[index]) * 100 : 0;
                        });
                    });
                }
                
                if (callbacks && callbacks.onFilterApplied) {
                    callbacks.onFilterApplied(data.chartData, data.filteredRowCount);
                }
            } else {
                alert('Error: ' + data.error);
            }
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error:', error);
            alert('Error applying chart filter. Please try again.');
        });
    },
    
    // Download chart HTML code
    downloadChartCode: function(options) {
        const loadingIndicator = document.getElementById('loading-indicator');
        loadingIndicator.classList.remove('hidden');
        
        // Include all necessary filter information and data
        const requestData = {
            chartType: this.selectedChartType,
            chartData: this.chartData,
            chartOptions: this.chartOptions,
            originalData: this.originalData,
            
            // Add these parameters to ensure we can regenerate data for all filter values
            filename: options.filename,
            sheet: options.sheet,
            xAxis: options.xAxis,
            yAxes: options.yAxes,
            filterColumn: options.filterColumn,
            filterValue: options.filterValue,
            startRow: options.startRow || 1,
            endRow: options.endRow,
            
            // Include chart settings
            ...options
        };
        
        console.log('Sending chart download request with data:', requestData);
        
        fetch('/download_chart_code', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify(requestData)
        })
        .then(response => {
            loadingIndicator.classList.add('hidden');
            
            if (response.ok) {
                return response.blob();
            } else {
                return response.json().then(errorData => {
                    throw new Error('Failed to download chart code: ' + (errorData.error || 'Unknown error'));
                });
            }
        })
        .then(blob => {
            // Create a URL for the blob
            const url = URL.createObjectURL(blob);
            
            // Create a link and trigger download
            const a = document.createElement('a');
            a.href = url;
            a.download = 'chart.html';
            document.body.appendChild(a);
            a.click();
            
            // Clean up
            setTimeout(() => {
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
            }, 100);
        })
        .catch(error => {
            loadingIndicator.classList.add('hidden');
            console.error('Error:', error);
            alert('Error downloading chart code: ' + error.message);
        });
    },
    
    // Create a chart on canvas
    createChart: function(canvas, chartData, chartType) {
        // Destroy existing chart if any
        if (this.currentChart) {
            this.currentChart.destroy();
        }
        
        this.chartData = chartData;
        this.selectedChartType = chartType;
        
        // Get the canvas context
        const ctx = canvas.getContext('2d');
        
        // Determine Chart.js chart type
        const chartJsType = this.getChartJsType(chartType);
        
        // Create chart options
        this.chartOptions = this.createChartOptions(chartType);
        
        // Ensure responsive layout
        this.chartOptions.responsive = true;
        this.chartOptions.maintainAspectRatio = false;
        
        // Ensure proper rendering in preview mode
        this.chartOptions.animation = {
            duration: 300
        };
        
        // Create chart
        this.currentChart = new Chart(ctx, {
            type: chartJsType,
            data: chartData,
            options: this.chartOptions
        });
        
        // Create custom legend if not exists
        this.createCustomLegend(chartData);
        
        // Initialize percentage values for stacked bar charts
        if (chartType === 'percentStackedBar') {
            setTimeout(() => this.recalculatePercentages(), 50);
        }
        
        return this.currentChart;
    },
    
    // Create custom legend with checkboxes
    createCustomLegend: function(chartData) {
        // Find or create legend container
        let legendContainer = document.getElementById('chartLegendContainer');
        if (!legendContainer) {
            legendContainer = document.createElement('div');
            legendContainer.id = 'chartLegendContainer';
            legendContainer.className = 'chart-legend-container';
            
            // Add to DOM - find the chart container and insert before it
            const chartContainer = document.querySelector('.chart-container');
            if (chartContainer) {
                chartContainer.insertBefore(legendContainer, chartContainer.firstChild);
            }
        }
        
        // Clear existing legend
        legendContainer.innerHTML = '';
        
        // Create legend items
        chartData.datasets.forEach((dataset, index) => {
            const item = document.createElement('div');
            item.className = 'legend-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.checked = true;
            checkbox.className = 'legend-checkbox';
            checkbox.dataset.index = index;
            
            const colorBox = document.createElement('span');
            colorBox.className = 'color-box';
            colorBox.style.backgroundColor = dataset.backgroundColor;
            
            const label = document.createElement('span');
            label.className = 'legend-label';
            label.textContent = dataset.label || `Dataset ${index + 1}`;
            
            item.appendChild(checkbox);
            item.appendChild(colorBox);
            item.appendChild(label);
            
            // Add click handler
            checkbox.addEventListener('change', (e) => {
                const index = parseInt(e.target.dataset.index, 10);
                const visibility = e.target.checked;
                
                // Update chart
                if (this.currentChart) {
                    this.currentChart.setDatasetVisibility(index, visibility);
                    this.currentChart.update();
                    
                    // For percentage stacked bar charts, recalculate percentages
                    if (this.selectedChartType === 'percentStackedBar') {
                        this.recalculatePercentages();
                    }
                }
            });
            
            legendContainer.appendChild(item);
        });
    },
    
    // Recalculate percentages for stacked bar chart
    recalculatePercentages: function() {
        if (!this.currentChart) return;
        
        // Get indices of visible datasets
        const visibleDatasets = [];
        this.currentChart.data.datasets.forEach((dataset, index) => {
            if (!this.currentChart.getDatasetMeta(index).hidden) {
                visibleDatasets.push(index);
            }
        });
        
        // Calculate totals for each data point using only visible datasets
        const totals = Array(this.currentChart.data.labels.length).fill(0);
        visibleDatasets.forEach(datasetIndex => {
            const dataset = this.currentChart.data.datasets[datasetIndex];
            
            // Get original raw values (not percentages)
            const originalValues = dataset.originalData || 
                                   (this.originalData?.datasets[datasetIndex]?.data) || 
                                   dataset.data;
            
            originalValues.forEach((value, index) => {
                // Only add value to total if it's not null
                if (value !== null && value !== undefined) {
                    totals[index] += Number(value) || 0;
                }
            });
        });
        
        // Update percentages for all datasets
        this.currentChart.data.datasets.forEach((dataset, datasetIndex) => {
            // Get original raw values (not percentages)
            const originalValues = dataset.originalData || 
                                   (this.originalData?.datasets[datasetIndex]?.data) || 
                                   dataset.data;
            
            // Calculate new percentages
            dataset.data = originalValues.map((value, index) => {
                // Preserve null values
                if (value === null || value === undefined) {
                    return null;
                }
                return totals[index] > 0 ? ((Number(value) || 0) / totals[index]) * 100 : 0;
            });
        });
        
        this.currentChart.update();
    },
    
    // Update existing chart with new data
    updateChart: function(chartData) {
        if (!this.currentChart) return;
        
        this.chartData = chartData;
        
        // Update chart datasets
        this.currentChart.data.labels = chartData.labels;
        
        // Update each dataset
        chartData.datasets.forEach((dataset, i) => {
            // If the dataset exists, update it
            if (i < this.currentChart.data.datasets.length) {
                this.currentChart.data.datasets[i].data = dataset.data;
            }
            // Otherwise add the new dataset
            else {
                this.currentChart.data.datasets.push(dataset);
            }
        });
        
        // Remove extra datasets if needed
        if (this.currentChart.data.datasets.length > chartData.datasets.length) {
            this.currentChart.data.datasets.splice(chartData.datasets.length);
        }
        
        // Update the chart
        this.currentChart.update();
    },
    
    // Create chart options based on chart type
    createChartOptions: function(chartType) {
        // Common options
        const options = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false, // Hide default legend, we'll use our custom one
                    position: 'top',
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            
                            // Handle different chart types
                            if (chartType === 'pie' || chartType === 'doughnut' || chartType === 'polarArea') {
                                let value = context.raw;
                                label += formatIndianNumber(value);
                            } else if (chartType === 'percentStackedBar') {
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y.toFixed(1) + '%';
                                }
                            } else if (chartType === 'scatter' || chartType === 'bubble') {
                                label += `(${formatIndianNumber(context.parsed.x)}, ${formatIndianNumber(context.parsed.y)})`;
                            } else {
                                if (context.parsed.y !== null) {
                                    label += formatIndianNumber(context.parsed.y);
                                }
                            }
                            
                            return label;
                        }
                    }
                }
            }
        };
        
        // For Chart.js v2 compatibility
        options.tooltips = {
            callbacks: {
                label: function(tooltipItem, data) {
                    let label = data.datasets[tooltipItem.datasetIndex].label || '';
                    if (label) {
                        label += ': ';
                    }
                    
                    if (chartType === 'percentStackedBar') {
                        if (tooltipItem.yLabel !== null) {
                            label += tooltipItem.yLabel.toFixed(1) + '%';
                        }
                    } else if (chartType === 'pie' || chartType === 'doughnut') {
                        let value = data.datasets[tooltipItem.datasetIndex].data[tooltipItem.index];
                        label += formatIndianNumber(value);
                    } else {
                        if (tooltipItem.yLabel !== null) {
                            label += formatIndianNumber(tooltipItem.yLabel);
                        }
                    }
                    
                    return label;
                }
            }
        };
        
        // Configure axes based on chart type
        if (chartType === 'bar' || chartType === 'horizontalBar') {
            // For Chart.js v3+
            options.scales = {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatIndianNumber(value);
                        }
                    }
                }
            };
            
            // For Chart.js v2 compatibility
            options.scales.xAxes = [{
                gridLines: {
                    display: false
                }
            }];
            options.scales.yAxes = [{
                ticks: {
                    beginAtZero: true,
                    callback: function(value) {
                        return formatIndianNumber(value);
                    }
                },
                gridLines: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }];
            
        } else if (chartType === 'stackedBar' || chartType === 'percentStackedBar') {
            // For Chart.js v3+
            options.scales = {
                x: {
                    stacked: true,
                    grid: {
                        display: false
                    }
                },
                y: {
                    stacked: true,
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            if (chartType === 'percentStackedBar') {
                                return value + '%';
                            } else {
                                return formatIndianNumber(value);
                            }
                        }
                    }
                }
            };
            
            // For Chart.js v2 compatibility
            options.scales.xAxes = [{
                stacked: true,
                gridLines: {
                    display: false
                }
            }];
            options.scales.yAxes = [{
                stacked: true,
                ticks: {
                    beginAtZero: true,
                    callback: function(value) {
                        if (chartType === 'percentStackedBar') {
                            return value + '%';
                        } else {
                            return formatIndianNumber(value);
                        }
                    }
                },
                gridLines: {
                    color: 'rgba(0, 0, 0, 0.1)'
                }
            }];
            
            // For percentage stacked bar, add data labels
            if (chartType === 'percentStackedBar') {
                options.plugins.datalabels = {
                    color: 'white',
                    font: {
                        weight: 'bold',
                        size: 13
                    },
                    formatter: function(value) {
                        // Handle null values
                        if (value === null || value === undefined) {
                            return '';
                        }
                        
                        // Format to 1 decimal place
                        const percentage = parseFloat(value).toFixed(1);
                        
                        // Only show if percentage is significant enough to display
                        return percentage > 3 ? percentage + '%' : '';
                    },
                    anchor: 'center',
                    align: 'center'
                };
            }
        } else if (chartType === 'line') {
            options.scales = {
                x: {
                    grid: {
                        display: false
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    },
                    ticks: {
                        callback: function(value) {
                            return formatIndianNumber(value);
                        }
                    }
                }
            };
        } else if (chartType === 'pie' || chartType === 'doughnut') {
            options.plugins.tooltip.callbacks.label = function(context) {
                const label = context.label || '';
                const value = context.raw;
                
                // Skip null values in total calculation
                const total = context.chart.data.datasets[0].data.reduce((a, b) => {
                    return a + (b !== null && b !== undefined ? b : 0);
                }, 0);
                
                // Handle null values in display
                if (value === null || value === undefined) {
                    return `${label}: No data`;
                }
                
                const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : 0;
                return `${label}: ${formatIndianNumber(value)} (${percentage}%)`;
            };
        } else if (chartType === 'scatter' || chartType === 'bubble') {
            options.scales = {
                x: {
                    grid: {
                        display: true,
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                },
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.1)'
                    }
                }
            };
        }
        
        return options;
    },
    
    // Convert our chart types to Chart.js types
    getChartJsType: function(type) {
        const typeMap = {
            'bar': 'bar',
            'horizontalBar': 'bar', // with indexAxis: 'y'
            'stackedBar': 'bar',
            'percentStackedBar': 'bar',
            'line': 'line',
            'pie': 'pie',
            'doughnut': 'doughnut',
            'radar': 'radar',
            'polarArea': 'polarArea',
            'scatter': 'scatter',
            'bubble': 'bubble'
        };
        
        return typeMap[type] || 'bar';
    },
    
    // Take a screenshot of the chart
    downloadChartImage: function(canvas, title) {
        if (!canvas) return;
        
        // Create a high-res version for download
        const link = document.createElement('a');
        
        // Set download filename
        link.download = (title || 'chart') + '.png';
        
        // Get chart as image
        link.href = canvas.toDataURL('image/png', 1.0);
        
        // Trigger download
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    }
};

// Format number in Indian format (e.g., 1,00,000)
export function formatIndianNumber(num) {
    if (num === null || num === undefined || isNaN(num)) return '';  // Return empty string for null values
    
    // Handle negative numbers
    let isNegative = false;
    if (num < 0) {
        isNegative = true;
        num = Math.abs(num);
    }
    
    // Format number to handle different magnitudes properly
    let formattedNumber;
    
    // For large numbers, use abbreviated format
    if (num >= 1000000000) {
        formattedNumber = (num / 1000000000).toFixed(1) + 'B';
    } else if (num >= 10000000) {
        formattedNumber = (num / 10000000).toFixed(1) + 'Cr';
    } else if (num >= 100000) {
        formattedNumber = (num / 100000).toFixed(1) + 'L';
    } else if (num >= 1000) {
        formattedNumber = (num / 1000).toFixed(1) + 'K';
    }
    // For numbers less than 1,000, no special formatting needed
    else if (num < 1000) {
        formattedNumber = num.toString();
    } else {
        // Convert to string and split at decimal point
        const parts = num.toString().split('.');
        let integerPart = parts[0];
        
        // First we get the last 3 digits
        const lastThree = integerPart.substring(integerPart.length - 3);
        // Then we get the remaining digits
        const remaining = integerPart.substring(0, integerPart.length - 3);
        
        // Now we format the remaining digits with commas after every 2 digits
        let formattedRemaining = '';
        if (remaining) {
            formattedRemaining = remaining.replace(/\B(?=(\d{2})+(?!\d))/g, ',');
        }
        
        // Combine the parts
        formattedNumber = formattedRemaining ? formattedRemaining + ',' + lastThree : lastThree;
        
        // Add decimal part if exists
        if (parts.length > 1) {
            formattedNumber += '.' + parts[1];
        }
    }
    
    // Add negative sign if needed
    if (isNegative) {
        formattedNumber = '-' + formattedNumber;
    }
    
    return formattedNumber;
} 
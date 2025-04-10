from flask import Blueprint, request, jsonify, send_file, current_app
import pandas as pd
import io
import os
import json
import numpy as np
from datetime import datetime
from chartgenerator.utils.helpers import calculate_percentage_data
from chartgenerator.utils.chart_processor import process_chart_data

chart_bp = Blueprint('chart_routes', __name__)

@chart_bp.route('/generate_chart', methods=['POST'])
def generate_chart():
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet')
    x_axis = data.get('xAxis')
    y_axes = data.get('yAxes', [])
    chart_type = data.get('chartType')
    filter_column = data.get('filterColumn')
    filter_value = data.get('filterValue')
    chart_filter_column = data.get('chartFilterColumn')
    start_row = data.get('startRow', 0)
    end_row = data.get('endRow')
    
    if not filename or not sheet_name or not x_axis or not y_axes or not chart_type:
        return jsonify({
            'success': False, 
            'error': 'Missing required parameters'
        })
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})
    
    try:
        # Read the sheet data with pandas
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Apply row range filter
        if start_row > 0:
            start_row = start_row - 2  # Adjust for Excel row numbering
            if start_row < 0:
                start_row = 0
        
        if end_row:
            end_row = end_row - 1  # Adjust for Excel row numbering
            df = df.iloc[start_row:end_row]
        else:
            df = df.iloc[start_row:]
        
        # Apply column filter if specified
        if filter_column and filter_value:
            df = df[df[filter_column] == filter_value]
        
        # Process data for chart
        chart_data = process_chart_data(df, x_axis, y_axes, chart_type)
        
        # Prepare chart filter values if specified
        chart_filter_values = []
        if chart_filter_column:
            chart_filter_values = df[chart_filter_column].dropna().unique().tolist()
        
        return jsonify({
            'success': True,
            'chartData': chart_data,
            'chartType': chart_type,
            'chartFilterValues': chart_filter_values
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@chart_bp.route('/apply_chart_filter', methods=['POST'])
def apply_chart_filter():
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet')
    x_axis = data.get('xAxis')
    y_axes = data.get('yAxes', [])
    chart_type = data.get('chartType')
    filter_column = data.get('filterColumn')
    filter_value = data.get('filterValue')
    chart_filter_column = data.get('chartFilterColumn')
    chart_filter_value = data.get('chartFilterValue')
    start_row = data.get('startRow', 0)
    end_row = data.get('endRow')
    
    if not filename or not sheet_name:
        return jsonify({
            'success': False, 
            'error': 'Missing required parameters'
        })
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})
    
    try:
        # Read the sheet data with pandas
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Apply row range filter
        if start_row > 0:
            start_row = start_row - 2
            if start_row < 0:
                start_row = 0
        
        if end_row:
            end_row = end_row - 1
            df = df.iloc[start_row:end_row]
        else:
            df = df.iloc[start_row:]
        
        # Apply main filter if specified
        if filter_column and filter_value:
            df = df[df[filter_column] == filter_value]
            
        # Apply chart filter if specified
        if chart_filter_column and chart_filter_value:
            df = df[df[chart_filter_column] == chart_filter_value]
        
        # Process data for chart
        chart_data = process_chart_data(df, x_axis, y_axes, chart_type)
        
        # Add information about visible datasets
        visible_indices = data.get('visibleDatasets')
        
        # For percentage stacked bar, ensure we always show 100%
        if chart_type == 'percentStackedBar' and chart_data and 'datasets' in chart_data:
            # If we have information about which datasets are visible, use it
            if visible_indices is not None:
                chart_data['datasets'] = calculate_percentage_data(
                    chart_data['datasets'], 
                    chart_data['labels'],
                    visible_indices
                )
            else:
                # Otherwise recalculate with all datasets
                chart_data['datasets'] = calculate_percentage_data(
                    chart_data['datasets'], 
                    chart_data['labels']
                )
        
        return jsonify({
            'success': True,
            'chartData': chart_data,
            'filteredRowCount': len(df)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@chart_bp.route('/download_chart_code', methods=['POST'])
def download_chart_code():
    """Generate and download a standalone HTML chart file"""
    try:
        # Extract request data
        data = request.json
        chart_type = data.get('chartType')
        chart_data = data.get('chartData')
        chart_options = data.get('chartOptions')
        
        # Determine the correct Chart.js chart type
        chartjs_type = chart_type
        if chart_type in ["stackedBar", "percentStackedBar", "horizontalBar"]:
            chartjs_type = "bar"
            
            # Add horizontal bar configuration
            if chart_type == "horizontalBar" and chart_options:
                if "scales" not in chart_options:
                    chart_options["scales"] = {}
                
                # Set horizontal bar options
                chart_options["indexAxis"] = "y"
                if "x" not in chart_options["scales"]:
                    chart_options["scales"]["x"] = {}
                chart_options["scales"]["x"]["beginAtZero"] = True
                
                if "y" not in chart_options["scales"]:
                    chart_options["scales"]["y"] = {}
                if "grid" not in chart_options["scales"]["y"]:
                    chart_options["scales"]["y"]["grid"] = {}
                chart_options["scales"]["y"]["grid"]["display"] = False
        
        # Add datalabels plugin configuration
        if "plugins" not in chart_options:
            chart_options["plugins"] = {}
            
        # Configure datalabels to show only for percentage stacked bar charts
        if chart_type == "percentStackedBar":
            chart_options["plugins"]["datalabels"] = {
                "display": True,
                "color": "white",
                "font": {
                    "weight": "bold",
                    "size": 12
                },
                "usePercentageFormatter": True,  # Flag to use percentage formatter
                "anchor": "center",
                "align": "center"
            }
        else:
            chart_options["plugins"]["datalabels"] = {
                "display": False
            }
        
        # Configure chart tooltips based on chart type
        if "tooltips" not in chart_options:
            chart_options["tooltips"] = {}
        
        if "callbacks" not in chart_options["tooltips"]:
            chart_options["tooltips"]["callbacks"] = {}
        
        # Set appropriate tooltip label callback based on chart type
        if chart_type == "percentStackedBar":
            chart_options["tooltips"]["callbacks"]["usePercentageFormatter"] = True
        elif chart_type in ["pie", "doughnut"]:
            chart_options["tooltips"]["callbacks"]["usePieFormatter"] = True
        else:
            chart_options["tooltips"]["callbacks"]["useIndianNumberFormatter"] = True
        
        # For Chart.js v3+ compatibility 
        if "plugins" not in chart_options:
            chart_options["plugins"] = {}
        
        if "tooltip" not in chart_options["plugins"]:
            chart_options["plugins"]["tooltip"] = {}
        
        if "callbacks" not in chart_options["plugins"]["tooltip"]:
            chart_options["plugins"]["tooltip"]["callbacks"] = {}
        
        # Set same callbacks for v3
        if chart_type == "percentStackedBar":
            chart_options["plugins"]["tooltip"]["callbacks"]["usePercentageFormatter"] = True
        elif chart_type in ["pie", "doughnut"]:
            chart_options["plugins"]["tooltip"]["callbacks"]["usePieFormatter"] = True
        else:
            chart_options["plugins"]["tooltip"]["callbacks"]["useIndianNumberFormatter"] = True
        
        # Configure chart options based on chart type
        if chart_type == "percentStackedBar":
            # Make sure stacked is set to true
            if "scales" not in chart_options:
                chart_options["scales"] = {}
            
            # For Chart.js v3+ format
            if "y" not in chart_options["scales"]:
                chart_options["scales"]["y"] = {}
            
            chart_options["scales"]["y"]["stacked"] = True
            chart_options["scales"]["y"]["min"] = 0
            chart_options["scales"]["y"]["max"] = 100
            
            if "x" not in chart_options["scales"]:
                chart_options["scales"]["x"] = {}
                
            chart_options["scales"]["x"]["stacked"] = True
            
            # For Chart.js v2 compatibility
            if "yAxes" not in chart_options["scales"]:
                chart_options["scales"]["yAxes"] = [{}]
            elif not isinstance(chart_options["scales"]["yAxes"], list):
                chart_options["scales"]["yAxes"] = [chart_options["scales"]["yAxes"]]
            
            if not chart_options["scales"]["yAxes"]:
                chart_options["scales"]["yAxes"].append({})
                
            chart_options["scales"]["yAxes"][0]["stacked"] = True
            chart_options["scales"]["yAxes"][0]["ticks"] = chart_options["scales"]["yAxes"][0].get("ticks", {})
            chart_options["scales"]["yAxes"][0]["ticks"]["min"] = 0
            chart_options["scales"]["yAxes"][0]["ticks"]["max"] = 100
            
            if "xAxes" not in chart_options["scales"]:
                chart_options["scales"]["xAxes"] = [{}]
            elif not isinstance(chart_options["scales"]["xAxes"], list):
                chart_options["scales"]["xAxes"] = [chart_options["scales"]["xAxes"]]
                
            if not chart_options["scales"]["xAxes"]:
                chart_options["scales"]["xAxes"].append({})
                
            chart_options["scales"]["xAxes"][0]["stacked"] = True

        # Convert v3 scale format to v2 format if needed for all chart types
        if chart_options and 'scales' in chart_options:
            scales = chart_options['scales']
            # Check if using v3 format (direct x/y properties)
            if 'x' in scales or 'y' in scales:
                new_scales = {}
                
                # Convert x to xAxes array if not already converted
                if 'x' in scales and 'xAxes' not in new_scales:
                    x_config = scales['x']
                    new_scales['xAxes'] = [{
                        'type': x_config.get('type', 'category'),
                        'display': x_config.get('display', True),
                        'scaleLabel': {
                            'display': x_config.get('title', {}).get('display', False),
                            'labelString': x_config.get('title', {}).get('text', ''),
                            'padding': x_config.get('title', {}).get('padding', {'top': 4, 'bottom': 4}),
                            'fontColor': x_config.get('title', {}).get('color', '#666'),
                        },
                        'gridLines': {
                            'display': x_config.get('grid', {}).get('display', False),
                            'color': x_config.get('grid', {}).get('color', 'rgba(0,0,0,0.1)'),
                            'lineWidth': x_config.get('grid', {}).get('lineWidth', 1),
                            'drawOnChartArea': x_config.get('grid', {}).get('drawOnChartArea', True),
                            'drawTicks': x_config.get('grid', {}).get('drawTicks', True),
                            'tickMarkLength': x_config.get('grid', {}).get('tickLength', 8),
                            'zeroLineWidth': x_config.get('grid', {}).get('zeroLineWidth', 1),
                            'zeroLineColor': x_config.get('grid', {}).get('zeroLineColor', 'rgba(0,0,0,0.25)'),
                        },
                        'ticks': x_config.get('ticks', {}),
                        'position': x_config.get('position', 'bottom'),
                        'offset': x_config.get('offset', False),
                        'id': x_config.get('id', 'x')
                    }]
                
                # Convert y to yAxes array with Indian format for tick values if not already converted
                if 'y' in scales and 'yAxes' not in new_scales:
                    y_config = scales['y']
                    ticks = y_config.get('ticks', {})
                    
                    # Add Indian number format callback for y-axis unless it's a percentage stacked bar
                    if chart_type != 'percentStackedBar':
                        # Instead of directly assigning the callback as a string,
                        # we'll handle this in the HTML template with a proper function
                        ticks['formatIndianNumbers'] = True
                    
                    new_scales['yAxes'] = [{
                        'type': y_config.get('type', 'linear'),
                        'display': y_config.get('display', True),
                        'scaleLabel': {
                            'display': y_config.get('title', {}).get('display', False),
                            'labelString': y_config.get('title', {}).get('text', ''),
                            'padding': y_config.get('title', {}).get('padding', {'top': 4, 'bottom': 4}),
                            'fontColor': y_config.get('title', {}).get('color', '#666'),
                        },
                        'gridLines': {
                            'display': y_config.get('grid', {}).get('display', True),
                            'color': y_config.get('grid', {}).get('color', 'rgba(0,0,0,0.1)'),
                            'lineWidth': y_config.get('grid', {}).get('lineWidth', 1),
                            'drawOnChartArea': y_config.get('grid', {}).get('drawOnChartArea', True),
                            'drawTicks': y_config.get('grid', {}).get('drawTicks', True),
                            'tickMarkLength': y_config.get('grid', {}).get('tickLength', 8),
                            'zeroLineWidth': y_config.get('grid', {}).get('zeroLineWidth', 1),
                            'zeroLineColor': y_config.get('grid', {}).get('zeroLineColor', 'rgba(0,0,0,0.25)'),
                        },
                        'ticks': ticks,
                        'position': y_config.get('position', 'left'),
                        'offset': y_config.get('offset', False),
                        'id': y_config.get('id', 'y'),
                        'beginAtZero': y_config.get('beginAtZero', True)
                    }]
                
                # Add any existing xAxes/yAxes from the original scales
                if 'xAxes' in scales:
                    new_scales['xAxes'] = scales['xAxes']
                if 'yAxes' in scales:
                    new_scales['yAxes'] = scales['yAxes']
                
                # Replace scales with converted format
                chart_options['scales'] = new_scales
        
        chart_title = data.get('chartTitle', 'Excel Data Chart')
        chart_description = data.get('chartDescription', '')
        chart_additional_info = data.get('chartAdditionalInfo', '')
        
        # Get filter information
        filter_column = data.get('chartFilterColumn', '')
        filter_values = data.get('chartFilterValues', [])
        selected_filter = data.get('chartFilterValue', '')
        
        # Get original data and visibility info
        visible_datasets = data.get('visibleDatasets', [])
        
        # Get main filters for data processing
        filename = data.get('filename')
        sheet_name = data.get('sheet')
        x_axis = data.get('xAxis')
        y_axes = data.get('yAxes', [])
        main_filter_column = data.get('filterColumn')
        main_filter_value = data.get('filterValue')
        start_row = data.get('startRow', 0)
        end_row = data.get('endRow')
        
        # Validate required fields
        if not chart_type or not chart_data:
            return jsonify({'success': False, 'error': 'Missing chart data'})
        
        # If this is a percentage stacked bar chart, pre-process the data to calculate percentages
        if chart_type == 'percentStackedBar' and 'datasets' in chart_data:
            # Create a copy of original data for later calculations
            original_data = {
                'labels': chart_data['labels'],
                'datasets': []
            }
            
            for dataset in chart_data['datasets']:
                original_data['datasets'].append({
                    'label': dataset['label'],
                    'backgroundColor': dataset['backgroundColor'],
                    'borderColor': dataset.get('borderColor'),
                    'data': dataset['data'].copy()  # Make a copy
                })
            
            # Calculate totals for each data point
            totals = [0] * len(chart_data['labels'])
            for dataset in chart_data['datasets']:
                for i, value in enumerate(dataset['data']):
                    totals[i] += float(value or 0)
            
            # Convert to percentages
            for dataset in chart_data['datasets']:
                for i in range(len(dataset['data'])):
                    if totals[i] > 0:
                        dataset['data'][i] = round((float(dataset['data'][i] or 0) / totals[i]) * 100, 1)
                    else:
                        dataset['data'][i] = 0
        
        # Process filter data if needed
        complete_filtered_data = {}
        
        if filter_column and filter_values and filename and sheet_name:
            # Generate data for each filter value
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                # Read the original sheet data
                df = pd.read_excel(filepath, sheet_name=sheet_name)
                
                # Apply main filters
                if start_row > 0:
                    start_row = start_row - 2
                    if start_row < 0:
                        start_row = 0
                
                if end_row:
                    end_row = end_row - 1
                    df = df.iloc[start_row:end_row]
                else:
                    df = df.iloc[start_row:]
                
                # Apply main column filter if specified
                if main_filter_column and main_filter_value:
                    df = df[df[main_filter_column] == main_filter_value]
                
                # Store the base data (no chart filter)
                no_filter_data = process_chart_data(df, x_axis, y_axes, chart_type)
                
                # Also pre-process percentages for filtered data if needed
                if chart_type == 'percentStackedBar' and 'datasets' in no_filter_data:
                    # Calculate totals
                    totals = [0] * len(no_filter_data['labels'])
                    for dataset in no_filter_data['datasets']:
                        for i, value in enumerate(dataset['data']):
                            totals[i] += float(value or 0)
                    
                    # Convert to percentages
                    for dataset in no_filter_data['datasets']:
                        for i in range(len(dataset['data'])):
                            if totals[i] > 0:
                                dataset['data'][i] = round((float(dataset['data'][i] or 0) / totals[i]) * 100, 1)
                            else:
                                dataset['data'][i] = 0
                
                complete_filtered_data["all"] = no_filter_data
                
                # Generate data for each filter value
                for filter_val in filter_values:
                    # Apply filter
                    filtered_df = df[df[filter_column] == filter_val]
                    # Process data
                    filter_chart_data = process_chart_data(filtered_df, x_axis, y_axes, chart_type)
                    
                    # Pre-process percentages for filtered data if needed
                    if chart_type == 'percentStackedBar' and 'datasets' in filter_chart_data:
                        # Calculate totals
                        totals = [0] * len(filter_chart_data['labels'])
                        for dataset in filter_chart_data['datasets']:
                            for i, value in enumerate(dataset['data']):
                                totals[i] += float(value or 0)
                        
                        # Convert to percentages
                        for dataset in filter_chart_data['datasets']:
                            for i in range(len(dataset['data'])):
                                if totals[i] > 0:
                                    dataset['data'][i] = round((float(dataset['data'][i] or 0) / totals[i]) * 100, 1)
                                else:
                                    dataset['data'][i] = 0
                    
                    # Store data
                    complete_filtered_data[filter_val] = filter_chart_data
        
        # Generate custom HTML with embedded chart
        html_template = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{chart_title}</title>
    <!-- Use Chart.js v2.9 for better compatibility -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@2.9.4/dist/Chart.min.js"></script>
    <!-- Old version of datalabels plugin that works with Chart.js v2 -->
    <script src="https://cdn.jsdelivr.net/npm/chartjs-plugin-datalabels@0.7.0/dist/chartjs-plugin-datalabels.min.js"></script>
    <link href="https://fonts.googleapis.com/css?family=Lato:300,400,700&display=swap" rel="stylesheet">
    <style>
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: 'Lato';
        }}
        
        body {{ 
            background-color: #f8f9fa;
            color: #333;
            padding: 30px;
        }}
        
        .chart-container {{ 
            max-width: 1000px; 
            margin: 0 auto;
            background-color: white;
            box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
            border-radius: 12px;
            padding: 30px;
            position: relative;
        }}
        
        .chart-header {{
            display: flex;
            justify-content: center;
            align-items: center;
            margin-bottom: 25px;
            position: relative;
        }}
        
        .chart-title {{
            text-align: center;
            font-size: 22px;
            font-weight: 700;
            color: #2c3e50;
            padding: 0 120px;
        }}
        
        .chart-logo {{
            position: absolute;
            top: 0;
            right: 0;
            width: 80px;
            height: auto;
        }}
        
        .chart-filter-controls {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 20px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .chart-filter-group {{
            display: flex;
            align-items: center;
        }}
        
        .chart-filter-group label {{
            margin-right: 12px;
            font-size: 14px;
            font-weight: 700;
            color: #555;
        }}
        
        .chart-filter-group select {{
            padding: 8px 12px;
            border: 1px solid #ddd;
            border-radius: 6px;
            font-size: 14px;
            min-width: 200px;
            font-family: 'Lato', sans-serif;
            background-color: white;
        }}
        
        .chart-canvas-container {{
            height: 550px;
            width: 100%;
            position: relative;
            margin-bottom: 30px;
        }}
        
        .chart-footer {{
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            margin-top: 25px;
            padding-top: 80px;
        }}
        
        .chart-info {{
            flex: 1;
            padding-right: 20px;
        }}
        
        .chart-description {{
            margin: 0 0 8px 0;
            padding: 0;
            font-size: 13px;
            color: #444;
            line-height: 1.4;
        }}
        
        .chart-additional-info {{
            margin: 0;
            padding: 0;
            font-size: 12px;
            color: #666;
            line-height: 1.4;
        }}
        
        .chart-actions {{
            display: flex;
            gap: 10px;
        }}
        
        .download-btn {{
            background-color: #4e73df;
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 8px;
            transition: all 0.2s ease;
        }}
        
        .download-btn:hover {{
            background-color: #3a5fc8;
            transform: translateY(-2px);
            box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        }}
        
        .hidden {{
            display: none;
        }}
        
        .chart-customization {{
            background-color: #f8f9fa;
            border-radius: 8px;
            padding: 15px;
            margin: 20px 0;
            box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        }}
        
        .chart-title-section, .axis-labels-section {{
            margin-bottom: 15px;
        }}
    </style>
</head>
<body>
    <div class="chart-container">
        <!-- Header with logo and title -->
        <div class="chart-header">
            <h1 class="chart-title">{chart_title}</h1>
            <img src="./static/images/logo.png" class="chart-logo" alt="Logo">
        </div>
        
        <!-- Chart canvas -->
        <div class="chart-canvas-container">
            <canvas id="myChart"></canvas>
        </div>
        
        <!-- Footer with description and download button -->
        <div class="chart-footer">
            <div class="chart-info">
                <p class="chart-description">{chart_description}</p>
                <p class="chart-additional-info">{chart_additional_info}</p>
            </div>
            <div class="chart-actions">
                <button class="download-btn" id="downloadImageBtn">
                    <svg xmlns="http://www.w3.org/2000/svg" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>
                </button>
            </div>
        </div>
    </div>
    
    <script>
        // Initialize chart when the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            // Register the datalabels plugin
            if (window.Chart && window['chartjs-plugin-datalabels']) {{
                Chart.plugins.register(window['chartjs-plugin-datalabels']);
            }}
            
            // Format number in Indian format (e.g., 1,00,000)
            function formatIndianNumber(num) {{
                if (num === null || num === undefined || isNaN(num)) return '';
                
                // Handle negative numbers
                let isNegative = false;
                if (num < 0) {{
                    isNegative = true;
                    num = Math.abs(num);
                }}
                
                // For numbers less than 1,000, no special formatting needed
                if (num < 1000) {{
                    return isNegative ? '-' + num.toString() : num.toString();
                }}
                
                // Convert to string and split at decimal point
                const parts = num.toString().split('.');
                let integerPart = parts[0];
                
                // First we get the last 3 digits
                const lastThree = integerPart.substring(integerPart.length - 3);
                // Then we get the remaining digits
                const remaining = integerPart.substring(0, integerPart.length - 3);
                
                // Format the remaining digits with commas after every 2 digits
                let formattedRemaining = '';
                if (remaining) {{
                    formattedRemaining = remaining.replace(/\\B(?=(\\d{{2}})+(?!\\d))/g, ',');
                }}
                
                // Combine the parts
                let result = formattedRemaining ? formattedRemaining + ',' + lastThree : lastThree;
                
                // Add decimal part if exists
                if (parts.length > 1) {{
                    result += '.' + parts[1];
                }}
                
                // Add negative sign if needed
                if (isNegative) {{
                    result = '-' + result;
                }}
                
                return result;
            }}
            
            // Add event listener for download button
            document.getElementById('downloadImageBtn').addEventListener('click', function() {{
                const canvas = document.getElementById('myChart');
                
                // Create a temporary canvas with white background for download
                const tempCanvas = document.createElement('canvas');
                tempCanvas.width = canvas.width;
                tempCanvas.height = canvas.height;
                const tempCtx = tempCanvas.getContext('2d');
                
                // Fill with white background
                tempCtx.fillStyle = 'white';
                tempCtx.fillRect(0, 0, tempCanvas.width, tempCanvas.height);
                
                // Draw the original chart on top
                tempCtx.drawImage(canvas, 0, 0);
                
                // Create download link
                const link = document.createElement('a');
                // Use a safe filename by replacing spaces with underscores
                const filename = '{chart_title}'.replace(/\\s+/g, '_') + '.png';
                link.download = filename;
                link.href = tempCanvas.toDataURL('image/png', 1.0);
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            }});
            
            // Create chart context
            const ctx = document.getElementById('myChart').getContext('2d');
            
            // Chart data
            const chartData = {json.dumps(chart_data)};
            
            // Chart options
            const options = {json.dumps(chart_options)};
            
            // Fix for tooltips - ensure they appear on hover with index mode
            // Set interaction mode to index (show all datasets at same x position)
            options.interaction = {{
                mode: 'index',
                intersect: false
            }};
            
            // Configure tooltips - make sure they are visible
            if (!options.plugins) {{
                options.plugins = {{}};
            }}
            if (!options.plugins.tooltip) {{
                options.plugins.tooltip = {{}};
            }}
            options.plugins.tooltip.enabled = true;
            options.plugins.tooltip.position = 'nearest';
            options.plugins.tooltip.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            options.plugins.tooltip.titleColor = 'white';
            options.plugins.tooltip.bodyColor = 'white';
            options.plugins.tooltip.borderColor = 'rgba(255, 255, 255, 0.2)';
            options.plugins.tooltip.borderWidth = 1;
            options.plugins.tooltip.padding = 10;
            
            // For Chart.js v2 compatibility
            if (!options.tooltips) {{
                options.tooltips = {{}};
            }}
            options.tooltips.enabled = true;
            options.tooltips.mode = 'index';
            options.tooltips.intersect = false;
            options.tooltips.position = 'nearest';
            options.tooltips.backgroundColor = 'rgba(0, 0, 0, 0.8)';
            options.tooltips.titleFontColor = 'white';
            options.tooltips.bodyFontColor = 'white';
            options.tooltips.borderColor = 'rgba(255, 255, 255, 0.2)';
            options.tooltips.borderWidth = 1;
            options.tooltips.xPadding = 10;
            options.tooltips.yPadding = 10;
            
            // Configure built-in chart legend
            if (!options.plugins) {{
                options.plugins = {{}};
            }}
            if (!options.plugins.legend) {{
                options.plugins.legend = {{}};
            }}
            
            // Enable the built-in legend with key labels
            options.plugins.legend.display = true;
            options.plugins.legend.position = 'top';
            
            // For Chart.js v2 compatibility
            if (!options.legend) {{
                options.legend = {{}};
            }}
            options.legend.display = true;
            options.legend.position = 'top';
            
            // Process the options to handle callbacks properly
            // Set up y-axis tick callbacks for Indian number formatting
            if (options.scales && options.scales.yAxes) {{
                options.scales.yAxes.forEach(yAxis => {{
                    if (yAxis.ticks && yAxis.ticks.formatIndianNumbers) {{
                        // Replace the flag with an actual callback function
                        yAxis.ticks.callback = function(value) {{
                            return formatIndianNumber(value);
                        }};
                        // Remove our temporary flag
                        delete yAxis.ticks.formatIndianNumbers;
                    }}
                }});
            }}
            
            // Set up datalabels formatter if needed
            if (options.plugins && options.plugins.datalabels) {{
                if (options.plugins.datalabels.usePercentageFormatter) {{
                    options.plugins.datalabels.formatter = function(value) {{
                        return value > 5 ? value.toFixed(1) + '%' : '';
                    }};
                    delete options.plugins.datalabels.usePercentageFormatter;
                }}
            }}
            
            // Configure tooltip callbacks based on chart type
            if (options.tooltips && options.tooltips.callbacks) {{
                const tooltipCallbacks = options.tooltips.callbacks;
                
                if (tooltipCallbacks.usePercentageFormatter) {{
                    tooltipCallbacks.label = function(tooltipItem, data) {{
                        var label = data.datasets[tooltipItem.datasetIndex].label || '';
                        if (label) {{
                            label += ': ';
                        }}
                        return label + tooltipItem.yLabel.toFixed(1) + '%';
                    }};
                    delete tooltipCallbacks.usePercentageFormatter;
                }}
                else if (tooltipCallbacks.usePieFormatter) {{
                    tooltipCallbacks.label = function(tooltipItem, data) {{
                        var label = data.labels[tooltipItem.index] || '';
                        var value = data.datasets[0].data[tooltipItem.index];
                        var total = data.datasets[0].data.reduce((a, b) => a + b, 0);
                        var percentage = ((value / total) * 100).toFixed(1);
                        return label + ': ' + formatIndianNumber(value) + ' (' + percentage + '%)';
                    }};
                    delete tooltipCallbacks.usePieFormatter;
                }}
                else if (tooltipCallbacks.useIndianNumberFormatter) {{
                    tooltipCallbacks.label = function(tooltipItem, data) {{
                        var label = data.datasets[tooltipItem.datasetIndex].label || '';
                        if (label) {{
                            label += ': ';
                        }}
                        return label + formatIndianNumber(tooltipItem.yLabel);
                    }};
                    delete tooltipCallbacks.useIndianNumberFormatter;
                }}
            }}
            
            // Do the same for Chart.js v3 tooltips
            if (options.plugins && options.plugins.tooltip && options.plugins.tooltip.callbacks) {{
                const tooltipCallbacks = options.plugins.tooltip.callbacks;
                
                if (tooltipCallbacks.usePercentageFormatter) {{
                    tooltipCallbacks.label = function(context) {{
                        var label = context.dataset.label || '';
                        if (label) {{
                            label += ': ';
                        }}
                        return label + context.parsed.y.toFixed(1) + '%';
                    }};
                    delete tooltipCallbacks.usePercentageFormatter;
                }}
                else if (tooltipCallbacks.usePieFormatter) {{
                    tooltipCallbacks.label = function(context) {{
                        var label = context.label || '';
                        var value = context.raw;
                        var total = context.chart.data.datasets[0].data.reduce((a, b) => a + b, 0);
                        var percentage = ((value / total) * 100).toFixed(1);
                        return label + ': ' + formatIndianNumber(value) + ' (' + percentage + '%)';
                    }};
                    delete tooltipCallbacks.usePieFormatter;
                }}
                else if (tooltipCallbacks.useIndianNumberFormatter) {{
                    tooltipCallbacks.label = function(context) {{
                        var label = context.dataset.label || '';
                        if (label) {{
                            label += ': ';
                        }}
                        return label + formatIndianNumber(context.parsed.y);
                    }};
                    delete tooltipCallbacks.useIndianNumberFormatter;
                }}
            }}
            
            // Add filter data if applicable
            {f"const filterData = {json.dumps(complete_filtered_data)};" if filter_column and filter_values else ""}
            
            // Function to filter chart data based on selected value
            function filterChartData() {{
                const filterValue = document.getElementById('chartFilter').value;
                const chart = window.myChart;
                
                if (!chart || !chart.data) return;
                
                // Store current dataset visibility
                const visibility = [];
                for (let i = 0; i < chart.data.datasets.length; i++) {{
                    visibility.push(!chart.getDatasetMeta(i).hidden);
                }}
                
                // Update chart based on filter selection
                if (!filterValue || filterValue === '') {{
                    // Use the "all" data (no filter)
                    if (filterData['all']) {{
                        chart.data.labels = filterData['all'].labels;
                        chart.data.datasets.forEach((dataset, i) => {{
                            if (i < filterData['all'].datasets.length) {{
                                dataset.data = filterData['all'].datasets[i].data;
                            }}
                        }});
                    }}
                }} else {{
                    // Use the specific filter value data
                    if (filterData[filterValue]) {{
                        chart.data.labels = filterData[filterValue].labels;
                        chart.data.datasets.forEach((dataset, i) => {{
                            if (i < filterData[filterValue].datasets.length) {{
                                dataset.data = filterData[filterValue].datasets[i].data;
                            }}
                        }});
                    }}
                }}
                
                // Restore dataset visibility
                for (let i = 0; i < chart.data.datasets.length; i++) {{
                    chart.getDatasetMeta(i).hidden = !visibility[i];
                }}
                
                chart.update();
            }}
            
            // Create filter controls if needed
            {f'''
            // Add filter controls to the DOM
            const filterControls = document.createElement('div');
            filterControls.className = 'chart-filter-controls';
            filterControls.innerHTML = 
                '<div class="chart-filter-group">' +
                    '<label for="chartFilter">Filter by {filter_column}:</label>' +
                    '<select id="chartFilter">' +
                        '<option value="">All Values</option>' +
                        '{' '.join([f'<option value="{val}"{" selected" if val == selected_filter else ""}>{val}</option>' for val in filter_values])}' +
                    '</select>' +
                '</div>';
            document.querySelector('.chart-header').insertAdjacentElement('afterend', filterControls);
            
            // Add event listener
            document.getElementById('chartFilter').addEventListener('change', filterChartData);
            ''' if filter_column and filter_values else ''}
            
            // Store original styling for datasets
            const originalStyles = [];
            
            // Add straight lines for line charts
            if ('{chartjs_type}' === 'line') {{
                if (!options.elements) {{
                    options.elements = {{}};
                }}
                if (!options.elements.line) {{
                    options.elements.line = {{}};
                }}
                options.elements.line.tension = 0; // Set to 0 for straight lines (no curves)
            }}
            
            // Create chart with proper datalabels plugin integration
            window.myChart = new Chart(ctx, {{
                type: '{chartjs_type}',
                data: chartData,
                options: options
            }});
            
            // Logic for highlighting closest dataset on hover (only for line charts)
            if ('{chartjs_type}' === 'line' && chartData.datasets.length > 1) {{
                // Store original styling
                chartData.datasets.forEach(dataset => {{
                    originalStyles.push({{
                        borderWidth: dataset.borderWidth || 2,
                        borderColor: dataset.borderColor,
                        backgroundColor: dataset.backgroundColor,
                        pointBorderColor: dataset.pointBorderColor || dataset.borderColor,
                        pointBackgroundColor: dataset.pointBackgroundColor || dataset.backgroundColor || dataset.borderColor,
                        pointRadius: dataset.pointRadius || 3,
                        pointHoverRadius: dataset.pointHoverRadius || 5,
                        tension: 0 // Always use straight lines
                    }});
                }});
                
                // Add mouse move handler to canvas
                const canvas = document.getElementById('myChart');
                
                canvas.addEventListener('mousemove', function(e) {{
                    const chart = window.myChart;
                    if (!chart) return;
                    
                    // Get positions relative to the canvas
                    const rect = canvas.getBoundingClientRect();
                    const x = e.clientX - rect.left;
                    const y = e.clientY - rect.top;
                    
                    // Find the closest x-value
                    const chartArea = chart.chartArea;
                    if (!chartArea || x < chartArea.left || x > chartArea.right || y < chartArea.top || y > chartArea.bottom) {{
                        // Mouse outside the chart area, reset styles
                        resetDatasetStyles();
                        chart.update();
                        return;
                    }}
                    
                    // Find nearest x point index
                    const xScale = chart.scales['x-axis-0'] || chart.scales.x;
                    if (!xScale) return;
                    
                    // Calculate the x value index in the data
                    const xPixelRange = chartArea.right - chartArea.left;
                    const xValueRange = xScale.max - xScale.min;
                    const xPercentage = (x - chartArea.left) / xPixelRange;
                    const dataPointIndex = Math.round(xPercentage * (chart.data.labels.length - 1));
                    
                    if (dataPointIndex < 0 || dataPointIndex >= chart.data.labels.length) return;
                    
                    // Find the dataset closest to the y position
                    const yScale = chart.scales['y-axis-0'] || chart.scales.y;
                    if (!yScale) return;
                    
                    let closestDistance = Infinity;
                    let closestDatasetIndex = -1;
                    
                    // Find visible datasets only
                    chart.data.datasets.forEach((dataset, datasetIndex) => {{
                        // Skip hidden datasets
                        if (chart.getDatasetMeta(datasetIndex).hidden) return;
                        
                        const value = dataset.data[dataPointIndex];
                        if (value === null || value === undefined) return;
                        
                        // Convert data point y-value to pixel position
                        const yPixel = yScale.getPixelForValue(value);
                        const distance = Math.abs(y - yPixel);
                        
                        if (distance < closestDistance) {{
                            closestDistance = distance;
                            closestDatasetIndex = datasetIndex;
                        }}
                    }});
                    
                    if (closestDatasetIndex !== -1) {{
                        // Update dataset styles
                        chart.data.datasets.forEach((dataset, datasetIndex) => {{
                            if (datasetIndex === closestDatasetIndex) {{
                                // Highlight the closest dataset
                                dataset.borderWidth = (originalStyles[datasetIndex].borderWidth + 1) || 3;
                                dataset.borderColor = originalStyles[datasetIndex].borderColor;
                                dataset.backgroundColor = originalStyles[datasetIndex].backgroundColor;
                                dataset.pointBorderColor = originalStyles[datasetIndex].pointBorderColor;
                                dataset.pointBackgroundColor = originalStyles[datasetIndex].pointBackgroundColor;
                                dataset.pointRadius = (originalStyles[datasetIndex].pointRadius + 1) || 4;
                                dataset.pointHoverRadius = (originalStyles[datasetIndex].pointHoverRadius + 2) || 7;
                                dataset.tension = 0; // Keep straight lines when highlighted
                            }} else {{
                                // Fade other datasets
                                const color = originalStyles[datasetIndex].borderColor;
                                let fadeColor;
                                
                                // Handle different color formats
                                if (color.startsWith('rgba')) {{
                                    // Already rgba format, just change opacity
                                    fadeColor = color.replace(/rgba\\(([^,]+),([^,]+),([^,]+),[^)]+\\)/, 'rgba($1,$2,$3,0.3)');
                                }} else if (color.startsWith('rgb')) {{
                                    // Convert rgb to rgba
                                    fadeColor = color.replace(/rgb\\(([^)]+)\\)/, 'rgba($1,0.3)');
                                }} else {{
                                    // Handle hex color or other formats (simplified)
                                    fadeColor = color;
                                }}
                                
                                dataset.borderWidth = (originalStyles[datasetIndex].borderWidth - 0.5) || 1;
                                dataset.borderColor = fadeColor;
                                dataset.pointBorderColor = fadeColor;
                                dataset.pointRadius = (originalStyles[datasetIndex].pointRadius - 1) || 2;
                                dataset.pointHoverRadius = originalStyles[datasetIndex].pointHoverRadius;
                                dataset.tension = 0; // Keep straight lines when faded
                            }}
                        }});
                        
                        // Update the chart with new styles
                        chart.update();
                    }}
                }});
                
                // Reset datasets when mouse leaves the chart
                canvas.addEventListener('mouseleave', function() {{
                    resetDatasetStyles();
                    window.myChart.update();
                }});
                
                // Reset all datasets to their original style
                function resetDatasetStyles() {{
                    window.myChart.data.datasets.forEach((dataset, datasetIndex) => {{
                        if (datasetIndex < originalStyles.length) {{
                            dataset.borderWidth = originalStyles[datasetIndex].borderWidth;
                            dataset.borderColor = originalStyles[datasetIndex].borderColor;
                            dataset.backgroundColor = originalStyles[datasetIndex].backgroundColor;
                            dataset.pointBorderColor = originalStyles[datasetIndex].pointBorderColor;
                            dataset.pointBackgroundColor = originalStyles[datasetIndex].pointBackgroundColor;
                            dataset.pointRadius = originalStyles[datasetIndex].pointRadius;
                            dataset.pointHoverRadius = originalStyles[datasetIndex].pointHoverRadius;
                            dataset.tension = 0; // Keep straight lines when reset
                        }}
                    }});
                }}
            }}
        }});
    </script>
</body>
</html>"""

        # Create a BytesIO object and send the file
        html_bytes = io.BytesIO()
        html_bytes.write(html_template.encode('utf-8'))
        html_bytes.seek(0)
        
        return send_file(
            html_bytes,
            mimetype='text/html',
            as_attachment=True,
            download_name='chart.html'
        )
    
    except Exception as e:
        # Return error with full traceback for debugging
        import traceback
        error_traceback = traceback.format_exc()
        return jsonify({
            'success': False, 
            'error': str(e),
            'traceback': error_traceback
        }) 
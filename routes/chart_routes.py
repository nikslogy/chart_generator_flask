from flask import Blueprint, request, jsonify, send_file, current_app, render_template
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
        # Read the sheet data with pandas, keeping NaN values (don't convert to 0)
        df = pd.read_excel(filepath, sheet_name=sheet_name, keep_default_na=True, na_values=[''])
        
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
        # Read the sheet data with pandas, keeping NaN values (don't convert to 0)
        df = pd.read_excel(filepath, sheet_name=sheet_name, keep_default_na=True, na_values=[''])
        
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
                # Use a special flag to indicate we need a percentage formatter
                "usePercentageFormatter": True,
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
                    if value is not None:  # Skip null values
                        totals[i] += float(value or 0)
            
            # Convert to percentages
            for dataset in chart_data['datasets']:
                for i in range(len(dataset['data'])):
                    if dataset['data'][i] is None:
                        continue  # Keep null values as null
                    elif totals[i] > 0:
                        dataset['data'][i] = round((float(dataset['data'][i] or 0) / totals[i]) * 100, 1)
                    else:
                        dataset['data'][i] = 0
        
        # Process filter data if needed
        complete_filtered_data = {}
        
        if filter_column and filter_values and filename and sheet_name:
            # Generate data for each filter value
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            if os.path.exists(filepath):
                # Read the original sheet data, keep NaN values
                df = pd.read_excel(filepath, sheet_name=sheet_name, keep_default_na=True, na_values=[''])
                
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
                            if value is not None:  # Skip null values
                                totals[i] += float(value or 0)
                    
                    # Convert to percentages
                    for dataset in no_filter_data['datasets']:
                        for i in range(len(dataset['data'])):
                            if dataset['data'][i] is None:
                                continue  # Keep null values as null
                            elif totals[i] > 0:
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
                                if value is not None:  # Skip null values
                                    totals[i] += float(value or 0)
                        
                        # Convert to percentages
                        for dataset in filter_chart_data['datasets']:
                            for i in range(len(dataset['data'])):
                                if dataset['data'][i] is None:
                                    continue  # Keep null values as null
                                elif totals[i] > 0:
                                    dataset['data'][i] = round((float(dataset['data'][i] or 0) / totals[i]) * 100, 1)
                                else:
                                    dataset['data'][i] = 0
                    
                    # Store data
                    complete_filtered_data[filter_val] = filter_chart_data
        
        # Generate custom HTML with embedded chart
        html_content = render_template(
            'chart_template.html',
            chart_title=chart_title,
            chart_description=chart_description,
            chart_additional_info=chart_additional_info,
            chart_data=json.dumps(chart_data),
            chart_options=json.dumps(chart_options),
            filter_column=filter_column,
            filter_values=filter_values,
            selected_filter=selected_filter,
            complete_filtered_data=json.dumps(complete_filtered_data),
            chartjs_type=chartjs_type
        )
        
        # Create a BytesIO object and send the file
        html_bytes = io.BytesIO()
        html_bytes.write(html_content.encode('utf-8'))
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
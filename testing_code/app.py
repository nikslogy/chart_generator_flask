from flask import Flask, render_template, request, jsonify, send_file
import pandas as pd
import io
import os
import json
import numpy as np
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload
app.config['ALLOWED_EXTENSIONS'] = {'xlsx', 'xls'}

# Create uploads folder if it doesn't exist
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'excelFile' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['excelFile']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        try:
            # Get all sheet names
            xls = pd.ExcelFile(filepath)
            sheet_names = xls.sheet_names
            
            return jsonify({
                'success': True, 
                'filename': filename,
                'sheets': sheet_names
            })
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)})
    
    return jsonify({'success': False, 'error': 'Invalid file type'})

@app.route('/get_sheet_data', methods=['POST'])
def get_sheet_data():
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet')
    
    if not filename or not sheet_name:
        return jsonify({'success': False, 'error': 'Missing filename or sheet name'})
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    if not os.path.exists(filepath):
        return jsonify({'success': False, 'error': 'File not found'})
    
    try:
        # Read the sheet data with pandas
        df = pd.read_excel(filepath, sheet_name=sheet_name)
        
        # Clean the data for JSON serialization
        df = df.replace({np.nan: None})
        
        # Get column names
        columns = df.columns.tolist()
        
        # Convert data to a list of dictionaries for easier processing in JavaScript
        data = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'columns': columns,
            'data': data,
            'rowCount': len(data)
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/filter_data', methods=['POST'])
def filter_data():
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet')
    filter_column = data.get('filterColumn')
    filter_value = data.get('filterValue')
    start_row = data.get('startRow', 0)
    end_row = data.get('endRow')
    
    if not filename or not sheet_name:
        return jsonify({'success': False, 'error': 'Missing filename or sheet name'})
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
        
        # Clean data for JSON serialization
        df = df.replace({np.nan: None})
        
        # Get unique values for chart filter
        unique_values = {}
        for col in df.columns:
            if df[col].dtype == object:  # Only get unique values for string columns
                unique_values[col] = df[col].dropna().unique().tolist()
        
        # Convert data to a list of dictionaries
        data = df.to_dict('records')
        
        return jsonify({
            'success': True,
            'data': data,
            'uniqueValues': unique_values
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/generate_chart', methods=['POST'])
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
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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
        if chart_type in ['pie', 'doughnut', 'polarArea']:
            # For single-series charts, only use the first y-axis
            if len(y_axes) > 0:
                y_axis = y_axes[0]['column']
                color = y_axes[0]['color']
                
                # Group by x-axis and sum y-values
                pie_data = df.groupby(x_axis)[y_axis].sum().reset_index()
                
                chart_data = {
                    'labels': pie_data[x_axis].tolist(),
                    'datasets': [{
                        'label': y_axis,
                        'data': pie_data[y_axis].tolist(),
                        'backgroundColor': generate_colors(len(pie_data)),
                        'borderColor': 'white',
                        'borderWidth': 1
                    }]
                }
        elif chart_type in ['scatter', 'bubble']:
            # For coordinate-based charts
            chart_data = {
                'datasets': []
            }
            
            for i, y_axis_info in enumerate(y_axes):
                y_axis = y_axis_info.get('column')
                color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
                
                dataset = {
                    'label': y_axis,
                    'backgroundColor': color,
                    'borderColor': color,
                    'borderWidth': 1,
                    'data': []
                }
                
                # Create data points with x,y coordinates
                for _, row in df.iterrows():
                    x_val = row[x_axis]
                    y_val = row[y_axis]
                    
                    if pd.notna(x_val) and pd.notna(y_val):
                        if chart_type == 'bubble':
                            # Use a third column for bubble size if available
                            size = 10  # Default size
                            if i + 1 < len(y_axes):
                                size_col = y_axes[i+1].get('column')
                                if size_col in row and pd.notna(row[size_col]):
                                    size = float(row[size_col])
                            point = {'x': float(x_val), 'y': float(y_val), 'r': size}
                        else:
                            point = {'x': float(x_val), 'y': float(y_val)}
                        dataset['data'].append(point)
                
                chart_data['datasets'].append(dataset)
        elif chart_type in ['stackedBar', 'percentStackedBar']:
            # For stacked bar charts
            # Group by x-axis and calculate sum for each y-axis
            pivoted_data = pd.pivot_table(df, values=y_axes[0]['column'], index=x_axis, aggfunc='sum')
            
            for i in range(1, len(y_axes)):
                y_axis = y_axes[i]['column']
                temp_pivot = pd.pivot_table(df, values=y_axis, index=x_axis, aggfunc='sum')
                pivoted_data = pd.merge(pivoted_data, temp_pivot, left_index=True, right_index=True)
            
            pivoted_data = pivoted_data.reset_index()
            
            # Create chart data structure
            chart_data = {
                'labels': pivoted_data[x_axis].tolist(),
                'datasets': []
            }
            
            # For each y-axis, create a dataset
            for i, y_axis_info in enumerate(y_axes):
                y_axis = y_axis_info.get('column')
                color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
                
                values = pivoted_data[y_axis].tolist()
                
                # For percentage stacked bars, convert to percentages
                if chart_type == 'percentStackedBar':
                    # Calculate totals for each x-axis label
                    totals = [0] * len(pivoted_data)
                    for j, y_info in enumerate(y_axes):
                        y_col = y_info.get('column')
                        for k, val in enumerate(pivoted_data[y_col].tolist()):
                            if not pd.isna(val):
                                totals[k] += abs(val)
                    
                    # Convert to percentages
                    percent_values = []
                    for j, val in enumerate(values):
                        if totals[j] > 0:
                            percent_values.append((abs(val) / totals[j]) * 100)
                        else:
                            percent_values.append(0)
                    
                    values = percent_values
                
                dataset = {
                    'label': y_axis,
                    'data': values,
                    'backgroundColor': color,
                    'borderColor': color,
                    'borderWidth': 1
                }
                
                chart_data['datasets'].append(dataset)
        else:
            # For standard charts (bar, line, radar)
            # Group by x-axis and calculate sum for each y-axis
            chart_data = {
                'labels': df[x_axis].unique().tolist(),
                'datasets': []
            }
            
            # Add datasets based on y-axes
            for i, y_axis_info in enumerate(y_axes):
                y_axis = y_axis_info.get('column')
                color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
                
                # Group by x-axis and sum y-values
                grouped_data = df.groupby(x_axis)[y_axis].sum().reset_index()
                
                # Create a dataframe with all possible x-axis values to handle missing values
                all_x = pd.DataFrame({x_axis: chart_data['labels']})
                merged_data = pd.merge(all_x, grouped_data, on=x_axis, how='left').fillna(0)
                
                dataset = {
                    'label': y_axis,
                    'data': merged_data[y_axis].tolist(),
                    'backgroundColor': color,
                    'borderColor': color,
                    'borderWidth': 1
                }
                
                # Additional properties for line charts
                if chart_type == 'line':
                    dataset['fill'] = False
                    dataset['tension'] = 0
                
                # Additional properties for radar charts
                if chart_type == 'radar':
                    dataset['fill'] = True
                    color_with_opacity = color.replace(')', ', 0.2)').replace('rgb', 'rgba')
                    dataset['backgroundColor'] = color_with_opacity
                
                chart_data['datasets'].append(dataset)
        
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

# Helper function to generate colors for pie/doughnut charts
def generate_colors(count):
    # Use a predefined color palette for better visual appeal
    color_palette = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#5a5c69', '#858796', '#4287f5', '#41e169'
    ]
    
    colors = []
    for i in range(count):
        colors.append(color_palette[i % len(color_palette)])
    return colors

# Helper function to calculate percentage data for stacked bar charts
def calculate_percentage_data(datasets, labels, visible_indices=None):
    # For each label/category, calculate the sum of all dataset values
    totals = [0] * len(labels)
    
    # If visible_indices is not provided, use all datasets
    if visible_indices is None:
        visible_indices = list(range(len(datasets)))
    
    # Sum only the visible datasets
    for idx in visible_indices:
        if idx < len(datasets):
            dataset = datasets[idx]
            for i, value in enumerate(dataset['data']):
                if i < len(totals):  # Ensure we don't go out of bounds
                    totals[i] += abs(float(value)) if value is not None else 0
    
    # Convert each dataset value to a percentage of the total
    percentage_datasets = []
    for idx, dataset in enumerate(datasets):
        percentage_data = []
        
        # Only process visible datasets for the result
        if idx in visible_indices:
            for i, value in enumerate(dataset['data']):
                if i < len(totals) and totals[i] > 0:
                    val = abs(float(value)) if value is not None else 0
                    percentage_data.append((val / totals[i]) * 100)
                else:
                    percentage_data.append(0)
            
            percentage_dataset = dataset.copy()
            percentage_dataset['data'] = percentage_data
            percentage_datasets.append(percentage_dataset)
        else:
            # For hidden datasets, include them with zeros
            percentage_dataset = dataset.copy()
            percentage_dataset['data'] = [0] * len(dataset['data'])
            percentage_datasets.append(percentage_dataset)
    
    return percentage_datasets

@app.route('/apply_chart_filter', methods=['POST'])
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
    
    filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
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

# Helper function to process chart data
def process_chart_data(df, x_axis, y_axes, chart_type):
    if chart_type in ['line']:
        if df.empty:
            return {'labels': [], 'datasets': []}
            
        # Get the unique x-axis values and sort them
        x_values = sorted(df[x_axis].dropna().unique().tolist())
        
        chart_data = {
            'labels': x_values,
            'datasets': []
        }
        
        for i, y_axis_info in enumerate(y_axes):
            y_axis = y_axis_info.get('column')
            color = y_axis_info.get('color', f'rgba(26, 19, 142, {0.8 if i == 0 else 0.6})')
            
            # Create a new dataframe for this dataset
            y_data = []
            
            for x_val in x_values:
                # Get rows matching this x value
                matching_rows = df[df[x_axis] == x_val]
                
                # Check if we have data for this point
                if matching_rows.empty or matching_rows[y_axis].isna().all():
                    # No data or all NaN values
                    y_data.append(None)  # Use None for missing data
                else:
                    # We have some data, sum it (ignoring NaNs)
                    y_data.append(matching_rows[y_axis].sum(skipna=True))
            
            # Create dataset with explicit None values for missing data
            dataset = {
                'label': y_axis,
                'data': y_data,
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1,
                'fill': False,
                'tension': 0,
                'spanGaps': False  # Don't connect points across null values
            }
            
            chart_data['datasets'].append(dataset)
        
        return chart_data
    
    elif chart_type in ['pie', 'doughnut', 'polarArea']:
        # For single-series charts, only use the first y-axis
        if len(y_axes) > 0:
            y_axis = y_axes[0]['column']
            
            # Group by x-axis and sum y-values
            pie_data = df.groupby(x_axis)[y_axis].sum().reset_index()
            
            chart_data = {
                'labels': pie_data[x_axis].tolist(),
                'datasets': [{
                    'label': y_axis,
                    'data': pie_data[y_axis].tolist(),
                    'backgroundColor': generate_colors(len(pie_data)),
                    'borderColor': 'white',
                    'borderWidth': 1
                }]
            }
            
            return chart_data
    
    elif chart_type in ['scatter', 'bubble']:
        # For coordinate-based charts
        chart_data = {
            'datasets': []
        }
        
        for i, y_axis_info in enumerate(y_axes):
            y_axis = y_axis_info.get('column')
            color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
            
            dataset = {
                'label': y_axis,
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1,
                'data': []
            }
            
            # Create data points with x,y coordinates
            for _, row in df.iterrows():
                x_val = row[x_axis]
                y_val = row[y_axis]
                
                if pd.notna(x_val) and pd.notna(y_val):
                    if chart_type == 'bubble':
                        # Use a third column for bubble size if available
                        size = 10  # Default size
                        if i + 1 < len(y_axes):
                            size_col = y_axes[i+1].get('column')
                            if size_col in row and pd.notna(row[size_col]):
                                size = float(row[size_col])
                        point = {'x': float(x_val), 'y': float(y_val), 'r': size}
                    else:
                        point = {'x': float(x_val), 'y': float(y_val)}
                    dataset['data'].append(point)
            
            chart_data['datasets'].append(dataset)
            
        return chart_data
    
    elif chart_type in ['stackedBar', 'percentStackedBar']:
        # For stacked bar charts
        # Group by x-axis and calculate sum for each y-axis
        if not y_axes:
            return {'labels': [], 'datasets': []}
            
        pivoted_data = pd.pivot_table(df, values=y_axes[0]['column'], index=x_axis, aggfunc='sum')
        
        for i in range(1, len(y_axes)):
            y_axis = y_axes[i]['column']
            temp_pivot = pd.pivot_table(df, values=y_axis, index=x_axis, aggfunc='sum')
            pivoted_data = pd.merge(pivoted_data, temp_pivot, left_index=True, right_index=True)
        
        pivoted_data = pivoted_data.reset_index()
        
        # Create chart data structure
        chart_data = {
            'labels': pivoted_data[x_axis].tolist(),
            'datasets': []
        }
        
        # For each y-axis, create a dataset
        for i, y_axis_info in enumerate(y_axes):
            y_axis = y_axis_info.get('column')
            color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
            
            values = pivoted_data[y_axis].tolist()
            
            # For percentage stacked bars, convert to percentages
            if chart_type == 'percentStackedBar':
                # Calculate totals for each x-axis label
                totals = [0] * len(pivoted_data)
                for j, y_info in enumerate(y_axes):
                    y_col = y_info.get('column')
                    for k, val in enumerate(pivoted_data[y_col].tolist()):
                        if not pd.isna(val):
                            totals[k] += abs(val)
                
                # Convert to percentages
                percent_values = []
                for j, val in enumerate(values):
                    if totals[j] > 0:
                        percent_values.append((abs(val) / totals[j]) * 100)
                    else:
                        percent_values.append(0)
                
                values = percent_values
            
            dataset = {
                'label': y_axis,
                'data': values,
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1
            }
            
            chart_data['datasets'].append(dataset)
            
        return chart_data
    
    else:
        # For standard charts (bar, line, radar)
        # Group by x-axis and calculate sum for each y-axis
        if df.empty:
            return {'labels': [], 'datasets': []}
            
        chart_data = {
            'labels': df[x_axis].unique().tolist(),
            'datasets': []
        }
        
        # Add datasets based on y-axes
        for i, y_axis_info in enumerate(y_axes):
            y_axis = y_axis_info.get('column')
            color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
            
            # Group by x-axis and sum y-values
            grouped_data = df.groupby(x_axis)[y_axis].sum().reset_index()
            
            # Create a dataframe with all possible x-axis values to handle missing values
            all_x = pd.DataFrame({x_axis: chart_data['labels']})
            merged_data = pd.merge(all_x, grouped_data, on=x_axis, how='left').fillna(0)
            
            dataset = {
                'label': y_axis,
                'data': merged_data[y_axis].tolist(),
                'backgroundColor': color,
                'borderColor': color,
                'borderWidth': 1
            }
            
            # Additional properties for line charts
            if chart_type == 'line':
                dataset['fill'] = False
                dataset['tension'] = 0
            
            # Additional properties for radar charts
            if chart_type == 'radar':
                dataset['fill'] = True
                color_with_opacity = color.replace(')', ', 0.2)').replace('rgb', 'rgba')
                dataset['backgroundColor'] = color_with_opacity
            
            chart_data['datasets'].append(dataset)
            
        return chart_data

@app.route('/download_chart_code', methods=['POST'])
def download_chart_code():
    data = request.json
    chart_type = data.get('chartType')
    chart_data = data.get('chartData')
    chart_options = data.get('chartOptions')
    chart_title = data.get('chartTitle', 'Excel Data Chart')
    chart_description = data.get('chartDescription', 'source')
    chart_additional_info = data.get('chartAdditionalInfo', 'comment')
    
    # Get filter information
    filter_column = data.get('chartFilterColumn', '')
    filter_values = data.get('chartFilterValues', [])
    selected_filter = data.get('chartFilterValue', '')
    
    # Get original data for filtering
    original_data = data.get('originalData', chart_data)
    visible_datasets = data.get('visibleDatasets', [])
    
    if not chart_type or not chart_data:
        return jsonify({'success': False, 'error': 'Missing chart data'})
    
    try:
        # Get current date
        from datetime import datetime
        current_date = datetime.now().strftime("%-m/%-d/%Y")
        
        # Format function needed for all charts
        format_function = """
        // Format number in Indian format (e.g., 1,00,000)
        function formatIndianNumber(num) {
            if (num === null || num === undefined || isNaN(num)) return '';  // Return empty string for null values
            
            // Handle negative numbers
            let isNegative = false;
            if (num < 0) {
                isNegative = true;
                num = Math.abs(num);
            }
            
            // Format number to handle different magnitudes properly
            let formattedNumber;
            
            // For numbers less than 1,000, no special formatting needed
            if (num < 1000) {
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
                    formattedRemaining = remaining.replace(/\\B(?=(\\d{{2}})+(?!\\d))/g, ',');
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
        """
        
        # Create extra_js with necessary functions
        extra_js = format_function
        
        # Add percentage stacked bar chart specific functions
        if chart_type == 'percentStackedBar':
            percentage_code = """
            // Store original data for percentage calculations
            const originalData = JSON.parse(JSON.stringify(chartData));
            
            // Function to recalculate percentages when toggling legend items
            function recalculatePercentages(chart) {
                // Get indices of visible datasets
                const visibleDatasets = [];
                chart.data.datasets.forEach((dataset, index) => {
                    if (!chart.getDatasetMeta(index).hidden) {
                        visibleDatasets.push(index);
                    }
                });
                
                // Calculate totals for each data point using only visible datasets
                const totals = Array(chart.data.labels.length).fill(0);
                visibleDatasets.forEach(datasetIndex => {
                    originalData.datasets[datasetIndex].data.forEach((value, index) => {
                        totals[index] += Math.abs(parseFloat(value) || 0);
                    });
                });
                
                // Update percentages for visible datasets
                chart.data.datasets.forEach((dataset, datasetIndex) => {
                    if (!chart.getDatasetMeta(datasetIndex).hidden) {
                        dataset.data = originalData.datasets[datasetIndex].data.map((value, index) => {
                            return totals[index] ? (Math.abs(parseFloat(value) || 0) / totals[index]) * 100 : 0;
                        });
                    }
                });
                
                chart.update();
            }
            """
            extra_js += "\n" + percentage_code
        
        # Add filter functionality if filter column is provided
        if filter_column and filter_values:
            filter_js = """
            // Function to filter chart data based on selected value
            function filterChartData() {
                const filterValue = document.getElementById('chartFilter').value;
                const chart = window.myChart;
                
                if (!chart || !chart.data) return;
                
                // Store current dataset visibility
                const visibility = [];
                chart.data.datasets.forEach((dataset, index) => {
                    visibility.push(!chart.getDatasetMeta(index).hidden);
                });
                
                // Reset to full data or filter based on selection
                if (!filterValue) {
                    // Use complete data
                    chart.data.labels = fullChartData.labels;
                    chart.data.datasets.forEach((dataset, i) => {
                        dataset.data = fullChartData.datasets[i].data;
                    });
                } else {
                    // Get the selected filter values
                    let selectedIndex = -1;
                    
                    // Find the index of the selected filter value
                    for (let i = 0; i < fullChartData.labels.length; i++) {
                        if (fullChartData.labels[i] === filterValue) {
                            selectedIndex = i;
                            break;
                        }
                    }
                    
                    if (selectedIndex !== -1) {
                        // Filter to show only the selected value
                        chart.data.labels = [fullChartData.labels[selectedIndex]];
                        
                        // Update each dataset
                        chart.data.datasets.forEach((dataset, i) => {
                            dataset.data = [fullChartData.datasets[i].data[selectedIndex]];
                        });
                    }
                }
                
                // Restore dataset visibility
                chart.data.datasets.forEach((dataset, index) => {
                    chart.getDatasetMeta(index).hidden = !visibility[index];
                });
                
                // For percentage stacked bar charts, recalculate percentages
                if (chart.config.type === 'bar' && 
                    chart.options.scales && 
                    chart.options.scales.y && 
                    chart.options.scales.y.stacked) {
                    if (typeof recalculatePercentages === 'function') {
                        recalculatePercentages(chart);
                    }
                } else {
                    chart.update();
                }
            }
            """
            extra_js += "\n" + filter_js
        
        # Prepare HTML template
        html_template = f"""<!DOCTYPE html>
<html>
<head>
    <title>{chart_title}</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <link href="https://fonts.googleapis.com/css?family=Lato" rel="stylesheet">
    <style>
        body {{ 
            font-family: Lato, Arial, sans-serif; 
            margin: 20px; 
            background-color: #f5f5f5;
        }}
        .chart-container {{ 
            max-width: 1000px; 
            margin: 0 auto 20px auto; 
            background-color: white;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            border-radius: 8px;
            padding: 20px;
        }}
        .chart-title {{
            text-align: center;
            font-size: 20px;
            font-weight: bold;
            margin-bottom: 20px;
            color: #2c3e50;
        }}
        .chart-filter-controls {{
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            background-color: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
        }}
        .chart-filter-group {{
            display: flex;
            align-items: center;
        }}
        .chart-filter-group label {{
            margin-right: 10px;
            font-size: 14px;
            color: #444;
        }}
        .chart-filter-group select {{
            padding: 6px 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
            min-width: 200px;
        }}
        .chart-canvas-container {{
            height: 500px;
            width: 100%;
        }}
        .chart-footer {{
            display: flex;
            justify-content: space-between;
            margin-top: 10px;
            padding-top: 5px;
            border-top: 1px solid #e9ecef;
        }}
        .chart-info {{
            flex: 1;
        }}
        .chart-description {{
            margin-top: 0;
            padding: 2px;
            font-size: 10px;
        }}
        .chart-additional-info {{
            margin-top: 2px;
            padding: 2px;
            font-size: 10px;
            color: #6c757d;
        }}
        .chart-date {{
            font-size: 12px;
            color: #6c757d;
            margin-left: 15px;
        }}
        .custom-legend {{
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            padding: 10px;
            margin-bottom: 10px;
        }}
        .legend-item {{
            display: flex;
            align-items: center;
            gap: 4px;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
        }}
        .hidden {{
            display: none;
        }}
    </style>
</head>
<body>
    <div class="chart-container">
        <div class="chart-title">{chart_title}</div>
        
        {f'''
        <div class="chart-filter-controls">
            <div class="chart-filter-group">
                <label for="chartFilter">Filter by {filter_column}:</label>
                <select id="chartFilter" onchange="filterChartData()">
                    <option value="">All Values</option>
                    {' '.join([f'<option value="{val}"{" selected" if val == selected_filter else ""}>{val}</option>' for val in filter_values])}
                </select>
            </div>
        </div>
        ''' if filter_column and filter_values else ''}
        
        <div class="chart-canvas-container">
            <canvas id="myChart"></canvas>
        </div>
        
        <div class="chart-footer">
            <div class="chart-info">
                <div class="chart-description">{chart_description}</div>
                <div class="chart-additional-info">{chart_additional_info}</div>
            </div>
            <div class="chart-date">{current_date}</div>
        </div>
    </div>
    
    <script>
        // Initialize chart when the page loads
        document.addEventListener('DOMContentLoaded', function() {{
            const ctx = document.getElementById('myChart').getContext('2d');

            // Format number in Indian format (e.g., 1,00,000)
            function formatIndianNumber(num) {{
                if (num === null || num === undefined || isNaN(num)) return '';  // Return empty string for null values
                
                // Handle negative numbers
                let isNegative = false;
                if (num < 0) {{
                    isNegative = true;
                    num = Math.abs(num);
                }}
                
                // Format number to handle different magnitudes properly
                let formattedNumber;
                
                // For numbers less than 1,000, no special formatting needed
                if (num < 1000) {{
                    formattedNumber = num.toString();
                }} else {{
                    // Convert to string and split at decimal point
                    const parts = num.toString().split('.');
                    let integerPart = parts[0];
                    
                    // First we get the last 3 digits
                    const lastThree = integerPart.substring(integerPart.length - 3);
                    // Then we get the remaining digits
                    const remaining = integerPart.substring(0, integerPart.length - 3);
                    
                    // Now we format the remaining digits with commas after every 2 digits
                    let formattedRemaining = '';
                    if (remaining) {{
                        formattedRemaining = remaining.replace(/\\B(?=(\\d{{2}})+(?!\\d))/g, ',');
                    }}
                    
                    // Combine the parts
                    formattedNumber = formattedRemaining ? formattedRemaining + ',' + lastThree : lastThree;
                    
                    // Add decimal part if exists
                    if (parts.length > 1) {{
                        formattedNumber += '.' + parts[1];
                    }}
                }}
                
                // Add negative sign if needed
                if (isNegative) {{
                    formattedNumber = '-' + formattedNumber;
                }}
                
                return formattedNumber;
            }}
            
            {extra_js}
            
            // Chart data (current filtered view)
            const chartData = {json.dumps(chart_data, indent=2)};
            
            // Full chart data for filtering
            const fullChartData = {json.dumps(original_data, indent=2)};
            
            // Chart options
            const options = {json.dumps(chart_options, indent=2)};
            
            // Ensure tooltip callbacks are properly configured
            if (!options.plugins) options.plugins = {{}};
            if (!options.plugins.tooltip) options.plugins.tooltip = {{}};
            if (!options.plugins.tooltip.callbacks) options.plugins.tooltip.callbacks = {{}};
            
            // Configure tooltips based on chart type
            if ('{chart_type}' === 'percentStackedBar') {{
                options.plugins.tooltip.callbacks.label = function(context) {{
                    let label = context.dataset.label || '';
                    if (label) {{
                        label += ': ';
                    }}
                    if (context.parsed.y !== null) {{
                        label += context.parsed.y.toFixed(1) + '%';
                    }}
                    return label;
                }};
            }} else if ('{chart_type}' === 'pie' || '{chart_type}' === 'doughnut' || '{chart_type}' === 'polarArea') {{
                options.plugins.tooltip.callbacks.label = function(context) {{
                    let label = context.label || '';
                    let value = context.raw;
                    if (label) {{
                        label += ': ';
                    }}
                    label += formatIndianNumber(value);
                    return label;
                }};
            }} else {{
                options.plugins.tooltip.callbacks.label = function(context) {{
                    let label = context.dataset.label || '';
                    if (label) {{
                        label += ': ';
                    }}
                    if (context.parsed.y !== null) {{
                        label += formatIndianNumber(context.parsed.y);
                    }}
                    return label;
                }};
            }}
            
            // Remove vertical grid lines
            if (!options.scales) options.scales = {{}};
            if (!options.scales.x) options.scales.x = {{}};
            if (!options.scales.x.grid) options.scales.x.grid = {{}};
            options.scales.x.grid.display = false;
            
            // Create chart
            window.myChart = new Chart(ctx, {{
                type: '{chart_type if chart_type not in ["stackedBar", "percentStackedBar", "horizontalBar"] else "bar"}',
                data: chartData,
                options: options
            }});
            
            // Create custom legend
            const legendContainer = document.createElement('div');
            legendContainer.className = 'custom-legend';
            document.querySelector('.chart-canvas-container').insertBefore(legendContainer, myChart);
            
            // Create legend items with checkboxes
            chartData.datasets.forEach((dataset, index) => {{
                const legendItem = document.createElement('div');
                legendItem.className = 'legend-item';
                legendItem.style.backgroundColor = dataset.backgroundColor + '15';
                legendItem.style.border = '1px solid ' + dataset.backgroundColor + '40';
                
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = {str(visible_datasets).lower() == '[]' or f"index in {str(visible_datasets)}" if chart_type == 'percentStackedBar' else 'true'};
                checkbox.style.cursor = 'pointer';
                checkbox.style.marginRight = '6px';
                
                const label = document.createElement('span');
                label.textContent = dataset.label || `Dataset ${{index + 1}}`;
                label.style.color = dataset.backgroundColor;
                label.style.cursor = 'pointer';
                
                legendItem.appendChild(checkbox);
                legendItem.appendChild(label);
                
                // Add click handlers
                [checkbox, label, legendItem].forEach(element => {{
                    element.addEventListener('click', (e) => {{
                        if (e.target !== checkbox) {{
                            checkbox.checked = !checkbox.checked;
                        }}
                        
                        const meta = window.myChart.getDatasetMeta(index);
                        meta.hidden = !checkbox.checked;
                        
                        // Update legend item appearance
                        legendItem.style.backgroundColor = checkbox.checked ? 
                            dataset.backgroundColor + '15' : 
                            '#f5f5f5';
                        label.style.color = checkbox.checked ? 
                            dataset.backgroundColor : 
                            '#999';
                        
                        // If it's a percentage stacked bar chart, recalculate percentages
                        if ('{chart_type}' === 'percentStackedBar') {{
                            recalculatePercentages(window.myChart);
                        }} else {{
                            window.myChart.update();
                        }}
                    }});
                }});
                
                legendContainer.appendChild(legendItem);
            }});
            
            // Initialize percentage stacked bar chart if needed
            {f"setTimeout(function() {{ recalculatePercentages(window.myChart); }}, 50);" if chart_type == 'percentStackedBar' else ""}
        }});
    </script>
</body>
</html>"""
        
        # Create a BytesIO object
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
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True)
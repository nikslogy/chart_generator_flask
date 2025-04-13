import pandas as pd
import numpy as np
from .helpers import generate_colors

def format_indian_number(num):
    """Format a number using Indian formatting (e.g., 1,00,000)"""
    if num is None:
        return ""
    
    # Convert to string
    num_str = str(num)
    
    # Check if the number is negative
    is_negative = num_str.startswith('-')
    if is_negative:
        num_str = num_str[1:]
    
    # Split the integer and decimal parts
    parts = num_str.split('.')
    integer_part = parts[0]
    
    # Format the integer part with commas
    if len(integer_part) <= 3:
        formatted = integer_part
    else:
        # Get the last 3 digits
        last_three = integer_part[-3:]
        # Get the remaining digits
        remaining = integer_part[:-3]
        
        # Format the remaining digits with commas after every 2 digits
        if remaining:
            groups = []
            i = len(remaining)
            while i > 0:
                start = max(0, i - 2)
                groups.insert(0, remaining[start:i])
                i = start
            
            formatted = ','.join(groups) + ',' + last_three
        else:
            formatted = last_three
    
    # Add the decimal part back if it exists
    if len(parts) > 1:
        formatted += '.' + parts[1]
    
    # Add the negative sign back if needed
    if is_negative:
        formatted = '-' + formatted
    
    return formatted

def process_chart_data(df, x_axis, y_axes, chart_type):
    """Process data for different chart types"""
    if chart_type in ['line']:
        return process_line_chart(df, x_axis, y_axes)
    elif chart_type in ['pie', 'doughnut', 'polarArea']:
        return process_pie_chart(df, x_axis, y_axes)
    elif chart_type in ['scatter', 'bubble']:
        return process_scatter_chart(df, x_axis, y_axes, chart_type)
    elif chart_type in ['stackedBar', 'percentStackedBar']:
        return process_stacked_bar_chart(df, x_axis, y_axes, chart_type)
    else:
        return process_standard_chart(df, x_axis, y_axes, chart_type)

def process_line_chart(df, x_axis, y_axes):
    """Process data for line charts"""
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

def process_pie_chart(df, x_axis, y_axes):
    """Process data for pie, doughnut and polar area charts"""
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
    return {'labels': [], 'datasets': []}

def process_scatter_chart(df, x_axis, y_axes, chart_type):
    """Process data for scatter and bubble charts"""
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

def process_stacked_bar_chart(df, x_axis, y_axes, chart_type):
    """Process data for stacked bar charts"""
    # For stacked bar charts
    # Group by x-axis and calculate sum for each y-axis
    if not y_axes:
        return {'labels': [], 'datasets': []}
    
    # Handle empty DataFrame case
    if df.empty:
        return {'labels': [], 'datasets': []}
        
    # Get all unique x-axis values upfront to ensure consistent labels
    all_x_values = sorted(df[x_axis].dropna().unique().tolist())
    
    # Create a new DataFrame with all x-axis values
    base_df = pd.DataFrame({x_axis: all_x_values})
    
    # Start with first y-axis
    pivoted_data = pd.pivot_table(df, values=y_axes[0]['column'], index=x_axis, aggfunc='sum')
    pivoted_data = pivoted_data.reset_index()
    
    # Make sure we include all x-axis values
    pivoted_data = pd.merge(base_df, pivoted_data, on=x_axis, how='left')
    
    # Add other y-axes
    for i in range(1, len(y_axes)):
        y_axis = y_axes[i]['column']
        temp_pivot = pd.pivot_table(df, values=y_axis, index=x_axis, aggfunc='sum')
        temp_pivot = temp_pivot.reset_index()
        
        # Make sure we include all x-axis values
        pivoted_data = pd.merge(pivoted_data, temp_pivot, on=x_axis, how='left')
    
    # Create chart data structure
    chart_data = {
        'labels': pivoted_data[x_axis].tolist(),
        'datasets': []
    }
    
    # For each y-axis, create a dataset
    for i, y_axis_info in enumerate(y_axes):
        y_axis = y_axis_info.get('column')
        color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
        
        values = []
        for val in pivoted_data[y_axis].tolist():
            # Preserve null/NaN values instead of converting to 0
            if pd.isna(val):
                values.append(None)
                print(f"Value is None: {val}")
            else:
                values.append(val)
                print(f"Value is not None: {val}")
        
        # For percentage stacked bars, convert to percentages
        if chart_type == 'percentStackedBar':
            # Calculate totals for each x-axis label
            totals = [0] * len(pivoted_data)
            for j, y_info in enumerate(y_axes):
                y_col = y_info.get('column')
                for k, val in enumerate(pivoted_data[y_col].tolist()):
                    if not pd.isna(val):
                        totals[k] += abs(val)
            
            # Convert to percentages while preserving null values
            percent_values = []
            for j, val in enumerate(values):
                if val is None:
                    percent_values.append(None)
                elif totals[j] > 0:
                    percent_values.append((abs(val) / totals[j]) * 100)
                else:
                    percent_values.append(0)
            
            values = percent_values
        
        dataset = {
            'label': y_axis,
            'data': values,
            'backgroundColor': color,
            'borderColor': color,
            'borderWidth': 1,
        }
        
        chart_data['datasets'].append(dataset)
        
    return chart_data

def process_standard_chart(df, x_axis, y_axes, chart_type):
    """Process data for standard charts (bar, radar)"""
    # For standard charts (bar, line, radar)
    # Group by x-axis and calculate sum for each y-axis
    if df.empty:
        return {'labels': [], 'datasets': []}
        
    # Get all unique x-axis values upfront to ensure consistent labels
    all_x_values = sorted(df[x_axis].dropna().unique().tolist())
    
    chart_data = {
        'labels': all_x_values,
        'datasets': []
    }
    
    # Add datasets based on y-axes
    for i, y_axis_info in enumerate(y_axes):
        y_axis = y_axis_info.get('column')
        color = y_axis_info.get('color', f'rgba(75, 192, 192, {0.8 if i == 0 else 0.6})')
        
        # Group by x-axis and sum y-values
        grouped_data = df.groupby(x_axis)[y_axis].sum().reset_index()
        
        # Create a dataframe with all possible x-axis values to handle missing values
        all_x = pd.DataFrame({x_axis: all_x_values})
        
        # Use left join but DON'T fill NaN values with 0
        merged_data = pd.merge(all_x, grouped_data, on=x_axis, how='left')
        
        # Convert NaN to None in the dataset
        values = []
        for val in merged_data[y_axis].tolist():
            if pd.isna(val):
                values.append(None)
            else:
                values.append(val)
        
        dataset = {
            'label': y_axis,
            'data': values,
            'backgroundColor': color,
            'borderColor': color,
            'borderWidth': 1
        }
        
        # Additional properties for line charts
        if chart_type == 'line':
            dataset['fill'] = False
            dataset['tension'] = 0
            dataset['spanGaps'] = False  # Add this for line charts to not connect points across null values
        
        # Additional properties for radar charts
        if chart_type == 'radar':
            dataset['fill'] = True
            color_with_opacity = color.replace(')', ', 0.2)').replace('rgb', 'rgba')
            dataset['backgroundColor'] = color_with_opacity
        
        chart_data['datasets'].append(dataset)
        
    return chart_data
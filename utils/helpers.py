import pandas as pd
import numpy as np

def allowed_file(filename, allowed_extensions):
    """Check if a file has an allowed extension"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in allowed_extensions

def generate_colors(count):
    """Generate colors for pie/doughnut charts"""
    # Use a predefined color palette for better visual appeal
    color_palette = [
        '#4e73df', '#1cc88a', '#36b9cc', '#f6c23e', '#e74a3b',
        '#6f42c1', '#5a5c69', '#858796', '#4287f5', '#41e169'
    ]
    
    colors = []
    for i in range(count):
        colors.append(color_palette[i % len(color_palette)])
    return colors

def calculate_percentage_data(datasets, labels, visible_indices=None):
    """Calculate percentage data for stacked bar charts"""
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
                if value is None:
                    # Preserve null values
                    percentage_data.append(None)
                elif i < len(totals) and totals[i] > 0:
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
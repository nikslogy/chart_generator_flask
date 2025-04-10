from flask import Blueprint, render_template, request, jsonify, current_app
import pandas as pd
import os
import numpy as np
from werkzeug.utils import secure_filename
from chartgenerator.utils.helpers import allowed_file

file_bp = Blueprint('file_routes', __name__)

@file_bp.route('/')
def index():
    return render_template('index.html')

@file_bp.route('/upload', methods=['POST'])
def upload_file():
    if 'excelFile' not in request.files:
        return jsonify({'success': False, 'error': 'No file part'})
    
    file = request.files['excelFile']
    if file.filename == '':
        return jsonify({'success': False, 'error': 'No file selected'})
    
    if file and allowed_file(file.filename, current_app.config['ALLOWED_EXTENSIONS']):
        filename = secure_filename(file.filename)
        filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

@file_bp.route('/get_sheet_data', methods=['POST'])
def get_sheet_data():
    data = request.json
    filename = data.get('filename')
    sheet_name = data.get('sheet')
    
    if not filename or not sheet_name:
        return jsonify({'success': False, 'error': 'Missing filename or sheet name'})
    
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
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

@file_bp.route('/filter_data', methods=['POST'])
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
import React from 'react';
import { formatFileSize } from '../../utils/helpers';

/**
 * GetDataCard — the OData equivalent of FileUpload. Deliberately mirrors
 * FileUpload's visual states (empty vs loaded, green confirmation card,
 * remove button) so the two flows read as siblings, not a bolted-on
 * afterthought — someone who used the old upload flow should recognize
 * this immediately.
 */
const GetDataCard = ({ processLabel, file, onGetData, onClear, isFetching, disabled }) => {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-semibold text-gray-700">ECC Data Source</h3>
        {file && (
          <span className="text-xs bg-green-100 text-green-700 px-2 py-1 rounded-full">
            Data loaded
          </span>
        )}
      </div>

      {!file ? (
        <div className="border-2 border-dashed border-gray-300 rounded-xl p-8 text-center">
          <div className="flex justify-center mb-3">
            <div className="p-3 bg-blue-50 rounded-full">
              <svg className="w-10 h-10 text-blue-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
              </svg>
            </div>
          </div>
          <p className="text-sm text-gray-600 mb-4">
            Fetch the current {processLabel} registry directly from ECC.
          </p>
          <button
            onClick={onGetData}
            disabled={disabled || isFetching}
            className="px-6 py-2.5 bg-blue-600 text-white rounded-lg hover:bg-blue-700
                       transition-colors font-medium text-sm disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isFetching ? 'Fetching from ECC...' : 'Get Data'}
          </button>
        </div>
      ) : (
        <div className="flex items-center gap-4 p-4 border-2 border-green-400 bg-green-50/50 rounded-xl">
          <div className="shrink-0 w-11 h-11 rounded-lg bg-green-100 flex items-center justify-center">
            <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.8} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
            </svg>
          </div>
          <div className="flex-1 min-w-0">
            <p className="font-semibold text-gray-800 truncate">{file.name}</p>
            <p className="text-sm text-gray-500">
              Fetched from ECC{file.size ? ` · ${formatFileSize(file.size)}` : ''}
            </p>
          </div>
          <button
            onClick={onClear}
            disabled={disabled}
            title="Clear and re-fetch"
            className="p-1.5 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      )}
    </div>
  );
};

export default GetDataCard;

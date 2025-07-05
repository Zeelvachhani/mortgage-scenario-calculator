<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Mortgage Scenario Calculator</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .input-row {
            display: flex;
            align-items: center;
            margin-bottom: 1rem;
        }
        .input-label {
            width: 180px;
            min-width: 180px;
            font-weight: 600;
        }
        .input-field {
            flex-grow: 1;
            min-width: 180px;
        }
        .optional-tag {
            font-size: 0.85em;
            color: #6b7280;
            margin-left: 0.5rem;
        }
        .required-asterisk {
            color: #ef4444;
        }
        .results-card {
            background-color: #f9fafb;
            border-radius: 0.5rem;
            padding: 1.5rem;
            box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
        }
    </style>
</head>
<body class="bg-gray-50 p-6">
    <div class="max-w-7xl mx-auto">
        <h1 class="text-3xl font-bold text-gray-800 mb-4">Mortgage Scenario Calculator</h1>
        <p class="text-gray-600 mb-8">Enter your mortgage parameters below. Results will appear on the right.</p>
        
        <div class="flex flex-col lg:flex-row gap-8">
            <!-- Left Column - Inputs -->
            <div class="w-full lg:w-2/5">
                <div class="bg-white rounded-lg shadow-md p-6">
                    <h2 class="text-xl font-semibold text-gray-800 mb-6">Input Parameters</h2>
                    
                    <div class="input-row">
                        <label class="input-label">Home Price $<span class="required-asterisk">*</span></label>
                        <input type="number" id="home_price" class="input-field border rounded-md px-3 py-2 w-full" min="0" step="10000">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">HOA $<span class="required-asterisk">*</span></label>
                        <input type="number" id="hoa" class="input-field border rounded-md px-3 py-2 w-full" min="0" step="10">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Property Tax %<span class="required-asterisk">*</span></label>
                        <input type="number" id="tax" class="input-field border rounded-md px-3 py-2" min="0" step="0.1">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Insurance %<span class="required-asterisk">*</span></label>
                        <input type="number" id="insurance" class="input-field border rounded-md px-3 py-2" min="0" step="0.1">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">PMI %<span class="required-asterisk">*</span></label>
                        <input type="number" id="pmi" class="input-field border rounded-md px-3 py-2" min="0" step="0.1">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Cash Available $<span class="required-asterisk">*</span></label>
                        <input type="number" id="cash" class="input-field border rounded-md px-3 py-2" min="0" step="10000">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Min Down Payment %</label>
                        <div class="input-field flex items-center">
                            <input type="text" class="border rounded-md px-3 py-2 w-full">
                            <span class="optional-tag">(optional)</span>
                        </div>
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Max Down Payment %</label>
                        <div class="input-field flex items-center">
                            <input type="text" class="border rounded-md px-3 py-2 flex-grow">
                            <span class="optional-tag">(optional)</span>
                        </div>
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Interest Rate %<span class="required-asterisk">*</span></label>
                        <input type="number" id="rate" class="input-field border rounded-md px-3 py-2" min="0" step="0.01">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Loan Term (Years)<span class="required-asterisk">*</span></label>
                        <input type="number" id="term" class="input-field border rounded-md px-3 py-2" min="1" step="1" value="30">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Monthly Liability $<span class="required-asterisk">*</span></label>
                        <input type="number" id="liability" class="input-field border rounded-md px-3 py-2" min="0" step="100">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Annual Income $<span class="required-asterisk">*</span></label>
                        <input type="number" id="income" class="input-field border rounded-md px-3 py-2" min="0" step="10000">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Max DTI %<span class="required-asterisk">*</span></label>
                        <input type="number" id="dti" class="input-field border rounded-md px-3 py-2" min="0" max="100" step="1">
                    </div>
                    
                    <div class="input-row">
                        <label class="input-label">Max Monthly Expense $</label>
                        <div class="input-field flex items-center">
                            <input type="text" class="border rounded-md px-3 py-2 flex-grow">
                            <span class="optional-tag">(optional)</span>
                        </div>
                    </div>
                    
                    <button class="mt-6 w-full bg-blue-600 hover:bg-blue-700 text-white font-medium py-2 px-4 rounded-md transition duration-150">
                        Calculate Scenarios
                    </button>
                </div>
            </div>
            
            <!-- Right Column - Results -->
            <div class="w-full lg:w-3/5">
                <div class="results-card h-full">
                    <h2 class="text-xl font-semibold text-gray-800 mb-4">Calculation Results</h2>
                    <div class="text-gray-500 italic">
                        Enter your parameters and click "Calculate Scenarios" to see the results.
                    </div>
                    <div id="results-container" class="mt-4 space-y-4 hidden">
                        <!-- Results will be displayed here -->
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        document.querySelector('button').addEventListener('click', function() {
            // Get input values
            const homePrice = parseFloat(document.getElementById('home_price').value);
            const hoa = parseFloat(document.getElementById('hoa').value) || 0;
            const propertyTaxRate = parseFloat(document.getElementById('tax').value) / 100;
            const insuranceRate = parseFloat(document.getElementById('insurance').value) / 100;
            const pmiRate = parseFloat(document.getElementById('pmi').value) / 100;
            const cashAvailable = parseFloat(document.getElementById('cash').value);
            const interestRate = parseFloat(document.getElementById('rate').value) / 100;
            const loanTerm = parseInt(document.getElementById('term').value);
            const monthlyLiabilities = parseFloat(document.getElementById('liability').value);
            const annualIncome = parseFloat(document.getElementById('income').value);
            const maxDTI = parseFloat(document.getElementById('dti').value) / 100;

            // Calculations (simplified example)
            const downPayment = Math.min(cashAvailable, homePrice * 0.2); // Max 20%
            const loanAmount = homePrice - downPayment;
            
            // Display results
            const resultsContainer = document.getElementById('results-container');
            resultsContainer.classList.remove('hidden');
            resultsContainer.innerHTML = `
                <div class="p-4 bg-white rounded-lg shadow">
                    <h3 class="font-bold text-lg mb-2">Mortgage Summary</h3>
                    <p>Loan Amount: ${loanAmount.toLocaleString()}</p>
                    <p>Down Payment: ${downPayment.toLocaleString()}</p>
                    <p>Monthly Payment: ${(loanAmount * (interestRate/12)).toFixed(2)}</p>
                </div>
            `;
        });
    </script>
</body>
</html>

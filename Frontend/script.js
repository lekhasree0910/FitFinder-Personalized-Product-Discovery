// FitFinder Client Engine
const API_BASE = (window.location.origin && (window.location.origin.includes(':5000') || window.location.port === '5000'))
    ? `${window.location.origin}/api`
    : 'http://127.0.0.1:5000/api';

// Current State
let currentQueryData = null;
let currentShortlist = [];
let selectedProductIds = new Set();
let currentUser = JSON.parse(localStorage.getItem('fitfinder_user') || 'null');

// DOM Content Loaded Handler
document.addEventListener('DOMContentLoaded', () => {
    updateAuthUI();
    initCategoryChips();
    initSamplePillListeners();
    initQueryInput();
    initCurrentPage();
    restorePreviousResultsIfAny();
});

// Update Navbar Authentication State
function updateAuthUI() {
    const authNav = document.getElementById('auth-nav-container');
    if (!authNav) return;

    if (currentUser) {
        authNav.innerHTML = `
            <span class="user-badge">👤 ${escapeHtml(currentUser.full_name || currentUser.email)}</span>
            <a href="history.html" class="nav-link">History</a>
            <button type="button" onclick="handleLogout()" class="btn btn-secondary" style="padding: 0.4rem 0.8rem; font-size: 0.85rem;">Logout</button>
        `;
    } else {
        authNav.innerHTML = `
            <a href="login.html" class="nav-link">Login</a>
            <a href="register.html" class="btn btn-primary" style="padding: 0.45rem 1rem; font-size: 0.85rem;">Sign Up</a>
        `;
    }
}

function handleLogout() {
    localStorage.removeItem('fitfinder_user');
    currentUser = null;
    fetch(`${API_BASE}/auth/logout/`, { method: 'POST' }).catch(() => {});
    window.location.href = 'index.html';
}

// Category Chips Handler
function initCategoryChips() {
    const chips = document.querySelectorAll('.chip-btn');
    chips.forEach(chip => {
        chip.addEventListener('click', (e) => {
            e.preventDefault();
            chips.forEach(c => c.classList.remove('active'));
            chip.classList.add('active');
        });
    });
}

function getSelectedCategory() {
    const activeChip = document.querySelector('.chip-btn.active');
    return activeChip ? activeChip.getAttribute('data-category') : 'Smartphone';
}

function selectCategory(categoryName) {
    const chips = document.querySelectorAll('.chip-btn');
    chips.forEach(chip => {
        if (chip.getAttribute('data-category') && chip.getAttribute('data-category').toLowerCase() === categoryName.toLowerCase()) {
            chip.classList.add('active');
        } else if (chip.getAttribute('data-category')) {
            chip.classList.remove('active');
        }
    });
}

// Sample Query Pills & Input listeners
function initSamplePillListeners() {
    const pills = document.querySelectorAll('.sample-pill');
    const textarea = document.getElementById('query-input');
    pills.forEach(pill => {
        pill.addEventListener('click', (e) => {
            e.preventDefault();
            if (textarea) {
                textarea.value = pill.innerText.replace(/^"|"$/g, '');
                const cat = pill.getAttribute('data-cat');
                if (cat) selectCategory(cat);
            }
        });
    });
}

function initQueryInput() {
    const textarea = document.getElementById('query-input');
    if (textarea) {
        textarea.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                submitChoiceAIQuery(e);
            }
        });
    }
}

// -------------------------------------------------------------
// ChoiceAI Query Submission
// -------------------------------------------------------------
async function submitChoiceAIQuery(e) {
    if (e && e.preventDefault) e.preventDefault();

    const textarea = document.getElementById('query-input');
    const queryText = textarea ? textarea.value.trim() : '';

    if (!queryText) {
        alert('Please enter your product requirements in plain English.');
        return false;
    }

    const category = getSelectedCategory();
    const btn = document.getElementById('btn-submit-query');
    if (btn) {
        btn.disabled = true;
        btn.innerText = '⚡ Extracting Preferences...';
    }

    try {
        const response = await fetch(`${API_BASE}/choiceai/query/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                raw_query_text: queryText,
                category: category,
                user_id: currentUser ? currentUser.user_id : 101
            })
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.error || 'Failed to analyze query.');
        }

        currentQueryData = data.query;

        // Store in BOTH sessionStorage and localStorage for rock-solid stability
        sessionStorage.setItem('current_query', JSON.stringify(data.query));
        sessionStorage.setItem('current_aspect_set', JSON.stringify(data.aspect_set));
        localStorage.setItem('current_query', JSON.stringify(data.query));
        localStorage.setItem('current_aspect_set', JSON.stringify(data.aspect_set));

        // Render persistent inline results on home page immediately
        await renderInlineResults(data.query);

        // Smoothly scroll down to the Matching Recommendations section
        const resultsSec = document.getElementById('results-section');
        if (resultsSec) {
            resultsSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

    } catch (err) {
        alert(`Error: ${err.message}`);
    } finally {
        if (btn) {
            btn.disabled = false;
            btn.innerText = '✨ Find My Match with ChoiceAI';
        }
    }
    return false;
}

// -------------------------------------------------------------
// Inline Results Rendering (Permanent & Non-disappearing)
// -------------------------------------------------------------
async function renderInlineResults(queryData) {
    const resultsSec = document.getElementById('results-section');
    if (!resultsSec) return;

    resultsSec.style.display = 'block';

    const catTag = document.getElementById('results-category-tag');
    if (catTag) catTag.innerText = queryData.category || 'Product';

    const budgetTag = document.getElementById('results-budget-tag');
    if (budgetTag) {
        budgetTag.innerText = queryData.budget ? `Budget: ₹${Number(queryData.budget).toLocaleString('en-IN')}` : 'Flexible Budget';
    }

    const qDisplay = document.getElementById('results-query-display');
    if (qDisplay) qDisplay.innerText = `"${queryData.raw_query_text}"`;

    const weightsContainer = document.getElementById('results-weights-tags');
    if (weightsContainer) {
        const weights = queryData.preference_weights_json || {};
        weightsContainer.innerHTML = Object.entries(weights)
            .map(([aspect, w]) => `
                <span class="chip-btn" style="padding: 0.3rem 0.75rem; font-size: 0.82rem; background: rgba(99, 102, 241, 0.15); border-color: rgba(99, 102, 241, 0.35); color: #c7d2fe; cursor: default;">
                    <strong style="text-transform: capitalize;">${escapeHtml(aspect)}</strong>: ${Math.round(w * 100)}%
                </span>
            `).join('');
    }

    const grid = document.getElementById('results-product-grid');
    if (grid) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2.5rem; color: #94a3b8;">🔍 Shortlisting matching products with CompareWise scoring...</div>';
    }

    try {
        const res = await fetch(`${API_BASE}/products/shortlist/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: queryData.category,
                budget: queryData.budget,
                preference_weights: queryData.preference_weights_json
            })
        });
        const data = await res.json();
        const prods = data.shortlisted_products || [];
        currentShortlist = prods;
        renderInlineCards(prods);
    } catch (err) {
        if (grid) grid.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #f43f5e;">Error loading products: ${err.message}</div>`;
    }
}

function renderInlineCards(products) {
    const grid = document.getElementById('results-product-grid');
    if (!grid) return;

    if (!products || products.length === 0) {
        grid.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem; color: #94a3b8;">No matching products found within this budget.</div>';
        return;
    }

    selectedProductIds.clear();
    products.slice(0, 3).forEach(p => selectedProductIds.add(p.product_id));
    updateHomeCompareButton();

    grid.innerHTML = '';
    products.forEach(p => {
        const isSelected = selectedProductIds.has(p.product_id);
        const card = document.createElement('div');
        card.className = `product-card ${isSelected ? 'selected' : ''}`;
        card.id = `home-card-${p.product_id}`;
        card.onclick = () => toggleHomeProductSelection(p.product_id);

        const aspectTags = Object.entries(p.aspect_scores || {})
            .slice(0, 3)
            .map(([k, v]) => `<span class="aspect-tag">${k}: ${Math.round(v * 100)}%</span>`)
            .join('');

        card.innerHTML = `
            <div class="product-img-wrapper">
                <img src="${p.image_url || 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500'}" class="product-img" alt="${escapeHtml(p.name)}" onerror="this.src='https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500'">
                <div class="match-badge">${p.match_percentage || Math.round((p.final_score || 0.75) * 100)}% Match</div>
            </div>
            <div class="product-body">
                <div class="product-brand">${escapeHtml(p.brand)}</div>
                <div class="product-name">${escapeHtml(p.name)}</div>
                <div class="product-price">₹${Number(p.price).toLocaleString('en-IN')}</div>
                <div class="aspect-tags">${aspectTags}</div>
                <button type="button" class="btn btn-secondary select-btn" style="margin-top: 0.5rem; font-size: 0.85rem; width: 100%;">
                    ${isSelected ? '✓ Selected for CompareWise' : '+ Select to Compare'}
                </button>
            </div>
        `;
        grid.appendChild(card);
    });
}

function toggleHomeProductSelection(productId) {
    if (selectedProductIds.has(productId)) {
        if (selectedProductIds.size === 1) {
            alert('Please keep at least 1 product selected for comparison.');
            return;
        }
        selectedProductIds.delete(productId);
    } else {
        if (selectedProductIds.size >= 4) {
            alert('You can compare up to 4 products at a time.');
            return;
        }
        selectedProductIds.add(productId);
    }

    const card = document.getElementById(`home-card-${productId}`);
    if (card) {
        const isSelected = selectedProductIds.has(productId);
        card.classList.toggle('selected', isSelected);
        const btn = card.querySelector('.select-btn');
        if (btn) btn.innerText = isSelected ? '✓ Selected for CompareWise' : '+ Select to Compare';
    }
    updateHomeCompareButton();
}

function updateHomeCompareButton() {
    const countSpan = document.getElementById('results-selected-count');
    if (countSpan) countSpan.innerText = selectedProductIds.size;
}

async function proceedToCompareFromHome() {
    if (selectedProductIds.size === 0) {
        alert('Please select at least 1 product to compare.');
        return;
    }

    const storedQuery = sessionStorage.getItem('current_query') || localStorage.getItem('current_query');
    const queryData = storedQuery ? JSON.parse(storedQuery) : (currentQueryData || {});

    const payload = {
        query_id: queryData.query_id,
        category: queryData.category || 'Smartphone',
        budget: queryData.budget,
        preference_weights: queryData.preference_weights_json,
        product_ids: Array.from(selectedProductIds)
    };

    try {
        const res = await fetch(`${API_BASE}/comparewise/compare/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to compute comparison.');

        sessionStorage.setItem('current_comparison_id', data.comparison_id);
        localStorage.setItem('current_comparison_id', data.comparison_id);
        window.location.href = 'compare.html';
    } catch (err) {
        alert(`Comparison Error: ${err.message}`);
    }
}

// -------------------------------------------------------------
// Preference Confirmation Modal & Slider Adjustments
// -------------------------------------------------------------
function openPreferenceConfirmationModal(queryData, aspectSet) {
    const modal = document.getElementById('pref-modal');
    if (!modal) return;

    if (!queryData) {
        const stored = sessionStorage.getItem('current_query') || localStorage.getItem('current_query');
        if (stored) queryData = JSON.parse(stored);
        else queryData = currentQueryData;
    }
    if (!queryData) return;

    document.getElementById('modal-query-text').innerText = `"${queryData.raw_query_text}"`;
    document.getElementById('modal-category').innerText = queryData.category;
    document.getElementById('modal-budget').innerText = queryData.budget ? `₹${Number(queryData.budget).toLocaleString('en-IN')}` : 'No limit specified';

    const weights = queryData.preference_weights_json || {};
    const container = document.getElementById('modal-weights-container');
    container.innerHTML = '';

    const aspects = aspectSet || Object.keys(weights);
    aspects.forEach(aspect => {
        const val = weights[aspect] !== undefined ? weights[aspect] : 0.20;
        const row = document.createElement('div');
        row.className = 'weight-row';
        row.innerHTML = `
            <div class="weight-label-row">
                <span style="text-transform: capitalize;">${escapeHtml(aspect)}</span>
                <span class="weight-val-badge" id="badge-${aspect}">${Math.round(val * 100)}%</span>
            </div>
            <input type="range" min="0" max="100" value="${Math.round(val * 100)}" id="slider-${aspect}" oninput="handleSliderChange('${aspect}', this.value)">
        `;
        container.appendChild(row);
    });

    modal.classList.add('active');
}

function closePreferenceModal() {
    const modal = document.getElementById('pref-modal');
    if (modal) modal.classList.remove('active');
}

function handleSliderChange(changedAspect, newValue) {
    const badge = document.getElementById(`badge-${changedAspect}`);
    if (badge) badge.innerText = `${newValue}%`;
}

async function normalizeAndConfirmWeights() {
    if (!currentQueryData) {
        const stored = sessionStorage.getItem('current_query') || localStorage.getItem('current_query');
        if (stored) currentQueryData = JSON.parse(stored);
    }
    if (!currentQueryData) return;

    const storedAspects = sessionStorage.getItem('current_aspect_set') || localStorage.getItem('current_aspect_set');
    const aspectSet = storedAspects ? JSON.parse(storedAspects) : Object.keys(currentQueryData.preference_weights_json || {});
    
    let rawSum = 0;
    const rawMap = {};

    aspectSet.forEach(aspect => {
        const slider = document.getElementById(`slider-${aspect}`);
        const val = slider ? parseFloat(slider.value) : 20;
        rawMap[aspect] = val;
        rawSum += val;
    });

    const normalized = {};
    if (rawSum === 0) rawSum = 1;

    let roundedSum = 0;
    aspectSet.forEach(aspect => {
        const norm = Math.round((rawMap[aspect] / rawSum) * 100) / 100;
        normalized[aspect] = norm;
        roundedSum += norm;
    });

    // Fix rounding discrepancies
    const diff = Math.round((1.0 - roundedSum) * 100) / 100;
    if (diff !== 0 && aspectSet.length > 0) {
        normalized[aspectSet[0]] = Math.round((normalized[aspectSet[0]] + diff) * 100) / 100;
    }

    currentQueryData.preference_weights_json = normalized;
    sessionStorage.setItem('current_query', JSON.stringify(currentQueryData));
    localStorage.setItem('current_query', JSON.stringify(currentQueryData));

    // Update inline section if on home page
    const resultsSec = document.getElementById('results-section');
    if (resultsSec) {
        await renderInlineResults(currentQueryData);
        closePreferenceModal();
        resultsSec.scrollIntoView({ behavior: 'smooth', block: 'start' });
    } else {
        closePreferenceModal();
        window.location.href = 'shortlist.html';
    }
}

// -------------------------------------------------------------
// Shortlist Page Logic
// -------------------------------------------------------------
async function loadShortlistPage() {
    let storedQuery = sessionStorage.getItem('current_query') || localStorage.getItem('current_query');
    let queryData = null;

    if (storedQuery) {
        try {
            queryData = JSON.parse(storedQuery);
        } catch (e) {
            queryData = null;
        }
    }

    if (!queryData) {
        // Safe default fallback so page NEVER crashes or bounces back to index.html
        queryData = {
            raw_query_text: "Top Recommended Smartphones with balanced camera and battery",
            category: "Smartphone",
            budget: 30000,
            preference_weights_json: { camera: 0.35, battery: 0.30, performance: 0.20, display: 0.15 }
        };
        sessionStorage.setItem('current_query', JSON.stringify(queryData));
        localStorage.setItem('current_query', JSON.stringify(queryData));
    }

    currentQueryData = queryData;

    document.getElementById('shortlist-query-display').innerText = `"${queryData.raw_query_text}"`;
    document.getElementById('shortlist-category-tag').innerText = queryData.category || 'Product';
    document.getElementById('shortlist-budget-tag').innerText = queryData.budget ? `Budget: ₹${Number(queryData.budget).toLocaleString('en-IN')}` : 'Flexible Budget';

    const container = document.getElementById('products-grid-container');
    container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 3rem; color: #94a3b8;">🔍 Finding and scoring matching candidates...</div>';

    try {
        const res = await fetch(`${API_BASE}/products/shortlist/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                category: queryData.category,
                budget: queryData.budget,
                preference_weights: queryData.preference_weights_json
            })
        });

        const data = await res.json();
        currentShortlist = data.shortlisted_products || [];
        renderShortlistCards(currentShortlist);
    } catch (err) {
        container.innerHTML = `<div style="grid-column: 1/-1; text-align: center; color: #f43f5e;">Error loading products: ${err.message}</div>`;
    }
}

function renderShortlistCards(products) {
    const container = document.getElementById('products-grid-container');
    if (!products || products.length === 0) {
        container.innerHTML = '<div style="grid-column: 1/-1; text-align: center; padding: 2rem;">No matching products found.</div>';
        return;
    }

    selectedProductIds.clear();
    // Auto-select top 3 candidates
    products.slice(0, 3).forEach(p => selectedProductIds.add(p.product_id));
    updateCompareButtonState();

    container.innerHTML = '';
    products.forEach((p, idx) => {
        const isSelected = selectedProductIds.has(p.product_id);
        const card = document.createElement('div');
        card.className = `product-card ${isSelected ? 'selected' : ''}`;
        card.id = `card-${p.product_id}`;
        card.onclick = () => toggleProductSelection(p.product_id);

        const aspectTags = Object.entries(p.aspect_scores || {})
            .slice(0, 3)
            .map(([k, v]) => `<span class="aspect-tag">${k}: ${Math.round(v * 100)}%</span>`)
            .join('');

        card.innerHTML = `
            <div class="product-img-wrapper">
                <img src="${p.image_url || 'https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500'}" class="product-img" alt="${escapeHtml(p.name)}" onerror="this.src='https://images.unsplash.com/photo-1511707171634-5f897ff02aa9?w=500'">
                <div class="match-badge">${p.match_percentage || Math.round(p.final_score * 100)}% Match</div>
            </div>
            <div class="product-body">
                <div class="product-brand">${escapeHtml(p.brand)}</div>
                <div class="product-name">${escapeHtml(p.name)}</div>
                <div class="product-price">₹${Number(p.price).toLocaleString('en-IN')}</div>
                <div class="aspect-tags">${aspectTags}</div>
                <button class="btn btn-secondary select-btn" style="margin-top: 0.5rem; font-size: 0.85rem; width: 100%;">
                    ${isSelected ? '✓ Selected for CompareWise' : '+ Select to Compare'}
                </button>
            </div>
        `;
        container.appendChild(card);
    });
}

function toggleProductSelection(productId) {
    if (selectedProductIds.has(productId)) {
        if (selectedProductIds.size === 1) {
            alert('Please keep at least 1 product selected for comparison.');
            return;
        }
        selectedProductIds.delete(productId);
    } else {
        if (selectedProductIds.size >= 4) {
            alert('You can compare up to 4 products at a time.');
            return;
        }
        selectedProductIds.add(productId);
    }

    // Update Card UI
    const card = document.getElementById(`card-${productId}`);
    if (card) {
        const isSelected = selectedProductIds.has(productId);
        card.classList.toggle('selected', isSelected);
        const btn = card.querySelector('.select-btn');
        if (btn) btn.innerText = isSelected ? '✓ Selected for CompareWise' : '+ Select to Compare';
    }

    updateCompareButtonState();
}

function updateCompareButtonState() {
    const btn = document.getElementById('btn-proceed-compare');
    if (btn) {
        btn.innerText = `⚖️ Compare ${selectedProductIds.size} Selected Products with CompareWise`;
    }
}

async function proceedToComparePage() {
    if (selectedProductIds.size === 0) {
        alert('Please select at least 1 product.');
        return;
    }

    const storedQuery = sessionStorage.getItem('current_query') || localStorage.getItem('current_query');
    const queryData = storedQuery ? JSON.parse(storedQuery) : (currentQueryData || {});

    const payload = {
        query_id: queryData.query_id,
        category: queryData.category || 'Smartphone',
        budget: queryData.budget,
        preference_weights: queryData.preference_weights_json,
        product_ids: Array.from(selectedProductIds)
    };

    try {
        const res = await fetch(`${API_BASE}/comparewise/compare/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Failed to compute comparison.');

        sessionStorage.setItem('current_comparison_id', data.comparison_id);
        localStorage.setItem('current_comparison_id', data.comparison_id);
        window.location.href = 'compare.html';
    } catch (err) {
        alert(`Comparison Error: ${err.message}`);
    }
}

// -------------------------------------------------------------
// CompareWise Recommendation & Table View
// -------------------------------------------------------------
async function loadComparePage() {
    const compId = sessionStorage.getItem('current_comparison_id') || localStorage.getItem('current_comparison_id') || 1;
    const bannerContainer = document.getElementById('recommendation-banner-container');

    try {
        // Fetch Side-by-side Table Data
        const res = await fetch(`${API_BASE}/comparewise/${compId}/table/`);
        if (!res.ok) {
            // Fallback attempt to comparison 1
            const fallbackRes = await fetch(`${API_BASE}/comparewise/1/table/`);
            if (fallbackRes.ok) {
                const tableData = await fallbackRes.json();
                renderRecommendationBanner(tableData);
                renderComparisonTable(tableData);
                return;
            }
            throw new Error('Comparison data not found. Please run a comparison from Discover.');
        }
        const tableData = await res.json();

        renderRecommendationBanner(tableData);
        renderComparisonTable(tableData);
    } catch (err) {
        if (bannerContainer) {
            bannerContainer.innerHTML = `
                <div style="background: rgba(244, 63, 94, 0.1); border: 1px solid rgba(244, 63, 94, 0.3); border-radius: var(--radius-md); padding: 2rem; text-align: center;">
                    <div style="color: #f43f5e; font-weight: 700; margin-bottom: 0.5rem; font-size: 1.1rem;">⚠️ ${escapeHtml(err.message)}</div>
                    <a href="index.html" class="btn btn-primary" style="margin-top: 1rem; font-size: 0.9rem;">Start New Discovery Query</a>
                </div>
            `;
        }
    }
}

function renderRecommendationBanner(data) {
    const bannerContainer = document.getElementById('recommendation-banner-container');
    if (!bannerContainer) return;

    const topProduct = data.rows.find(r => r.is_top_recommendation) || data.rows[0];
    if (!topProduct) return;

    const expl = topProduct.explanation || {};
    const strengths = expl.strengths_text || 'Scores strongly across all prioritized feature categories.';
    const weakness = expl.weakness_text || 'Relatively lower score in minor secondary aspects.';

    bannerContainer.innerHTML = `
        <div class="recommendation-banner">
            <div class="rec-header">
                <div>
                    <div class="rec-badge">🏆 TOP COMPAREWISE RECOMMENDATION</div>
                    <h2 style="font-family: var(--font-heading); font-size: 2rem; margin-top: 0.5rem;">
                        ${escapeHtml(topProduct.brand)} ${escapeHtml(topProduct.name)}
                    </h2>
                    <div style="font-size: 1.25rem; font-weight: 700; color: #a5b4fc; margin-top: 0.25rem;">
                        ₹${Number(topProduct.price).toLocaleString('en-IN')}
                    </div>
                </div>
                <div class="rec-score-circle">
                    <div class="rec-score-num">${topProduct.match_percentage}%</div>
                    <div class="rec-score-lbl">Match Score</div>
                </div>
            </div>

            <div class="rec-content-grid">
                <div>
                    <div class="grounded-box strengths-box">
                        <div class="grounded-title">✨ Grounded Strengths (ABSA Verified)</div>
                        <p class="grounded-text">${escapeHtml(strengths)}</p>
                    </div>
                    <div class="grounded-box weakness-box">
                        <div class="grounded-title">⚠️ Grounded Weakness Callout</div>
                        <p class="grounded-text">${escapeHtml(weakness)}</p>
                    </div>
                </div>

                <div class="glass-card" style="padding: 1.25rem; background: rgba(10, 13, 20, 0.4);">
                    <div style="font-weight: 700; font-size: 0.95rem; margin-bottom: 0.75rem; color: #f8fafc;">
                        📊 Feature Weight vs. Aspect Score Breakdown
                    </div>
                    ${renderFeatureContributionBars(topProduct.aspects, data.preference_weights)}
                </div>
            </div>
        </div>
    `;
}

function renderFeatureContributionBars(aspects, weights) {
    return Object.entries(aspects || {}).map(([aspect, score]) => {
        const weight = weights[aspect] || 0.15;
        const scorePct = Math.round(score * 100);
        const weightPct = Math.round(weight * 100);

        return `
            <div style="margin-bottom: 0.75rem;">
                <div style="display: flex; justify-content: space-between; font-size: 0.8rem; font-weight: 600;">
                    <span style="text-transform: capitalize;">${aspect} <span style="color: #94a3b8; font-weight: 400;">(Weight: ${weightPct}%)</span></span>
                    <span style="color: #34d399;">${scorePct}%</span>
                </div>
                <div class="progress-bar-bg">
                    <div class="progress-bar-fill" style="width: ${scorePct}%;"></div>
                </div>
            </div>
        `;
    }).join('');
}

function renderComparisonTable(data) {
    const tableContainer = document.getElementById('compare-table-container');
    if (!tableContainer) return;

    const headers = data.aspect_headers || [];

    const headerHtml = `
        <thead>
            <tr>
                <th>Product</th>
                <th>Price</th>
                <th>Personalized Match</th>
                ${headers.map(h => `<th style="text-transform: capitalize;">${h}</th>`).join('')}
            </tr>
        </thead>
    `;

    const rowsHtml = data.rows.map(r => {
        const isWinner = r.is_top_recommendation;
        return `
            <tr class="${isWinner ? 'winner-row' : ''}">
                <td style="font-weight: 700;">
                    ${isWinner ? '<span style="color: #f59e0b; margin-right: 4px;">👑</span>' : ''}
                    ${escapeHtml(r.brand)} ${escapeHtml(r.name)}
                </td>
                <td style="font-weight: 600; color: #a5b4fc;">
                    ₹${Number(r.price).toLocaleString('en-IN')}
                </td>
                <td>
                    <span style="font-weight: 800; color: ${isWinner ? '#34d399' : '#f8fafc'};">
                        ${r.match_percentage}%
                    </span>
                </td>
                ${headers.map(h => {
                    const val = r.aspects[h] || 0.70;
                    return `<td><span class="weight-val-badge">${Math.round(val * 100)}%</span></td>`;
                }).join('')}
            </tr>
        `;
    }).join('');

    tableContainer.innerHTML = `
        <div class="table-wrapper">
            <table class="compare-table">
                ${headerHtml}
                <tbody>
                    ${rowsHtml}
                </tbody>
            </table>
        </div>
    `;
}

// -------------------------------------------------------------
// History Page Logic
// -------------------------------------------------------------
async function loadHistoryPage() {
    const container = document.getElementById('history-container');
    if (!container) return;

    const userId = currentUser ? currentUser.user_id : 101;

    try {
        const res = await fetch(`${API_BASE}/users/${userId}/history/`);
        const data = await res.json();
        const history = data.history || [];

        if (history.length === 0) {
            container.innerHTML = '<div style="text-align: center; padding: 3rem; color: #94a3b8;">No query history yet. Try asking ChoiceAI!</div>';
            return;
        }

        container.innerHTML = history.map(item => {
            const q = item.query;
            const hasComps = item.comparisons && item.comparisons.length > 0;
            const compId = hasComps ? item.comparisons[0].comparison_id : null;

            return `
                <div class="glass-card" style="margin-bottom: 1.25rem; display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem;">
                    <div>
                        <div style="font-size: 0.8rem; color: var(--accent-cyan); font-weight: 700; text-transform: uppercase;">
                            ${q.category} • ${q.budget ? '₹' + Number(q.budget).toLocaleString('en-IN') : 'No budget'}
                        </div>
                        <div style="font-size: 1.1rem; font-weight: 600; margin: 0.25rem 0;">
                            "${escapeHtml(q.raw_query_text)}"
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-dim);">
                            Submitted on: ${new Date(q.submitted_at).toLocaleString()}
                        </div>
                    </div>
                    <div>
                        ${compId ? `<button onclick="reopenComparison(${compId})" class="btn btn-emerald" style="font-size: 0.85rem; padding: 0.5rem 1rem;">Re-open CompareWise</button>` : ''}
                        <button onclick="relaunchQuery(${JSON.stringify(q).replace(/"/g, '&quot;')})" class="btn btn-secondary" style="font-size: 0.85rem; padding: 0.5rem 1rem;">Re-run Query</button>
                    </div>
                </div>
            `;
        }).join('');
    } catch (err) {
        container.innerHTML = `<div style="color: #f43f5e;">Failed to load history: ${err.message}</div>`;
    }
}

function reopenComparison(comparisonId) {
    sessionStorage.setItem('current_comparison_id', comparisonId);
    window.location.href = 'compare.html';
}

function relaunchQuery(queryObj) {
    sessionStorage.setItem('current_query', JSON.stringify(queryObj));
    window.location.href = 'shortlist.html';
}

// -------------------------------------------------------------
// Authentication Forms Logic
// -------------------------------------------------------------
async function handleRegisterSubmit(e) {
    e.preventDefault();
    const fullName = document.getElementById('reg-name').value.trim();
    const email = document.getElementById('reg-email').value.trim();
    const password = document.getElementById('reg-password').value.trim();

    try {
        const res = await fetch(`${API_BASE}/auth/register/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ full_name: fullName, email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Registration failed');

        localStorage.setItem('fitfinder_user', JSON.stringify(data.user));
        window.location.href = 'index.html';
    } catch (err) {
        alert(err.message);
    }
}

async function handleLoginSubmit(e) {
    e.preventDefault();
    const email = document.getElementById('login-email').value.trim();
    const password = document.getElementById('login-password').value.trim();

    try {
        const res = await fetch(`${API_BASE}/auth/login/`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ email, password })
        });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Login failed');

        localStorage.setItem('fitfinder_user', JSON.stringify(data.user));
        window.location.href = 'index.html';
    } catch (err) {
        alert(err.message);
    }
}

// Helper: Escape HTML
function escapeHtml(str) {
    if (!str) return '';
    return String(str)
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

// Page-specific initialization
function initCurrentPage() {
    const path = window.location.pathname.toLowerCase();
    if (path.endsWith('shortlist.html')) {
        loadShortlistPage();
    } else if (path.endsWith('compare.html')) {
        loadComparePage();
    } else if (path.endsWith('history.html')) {
        loadHistoryPage();
    }
}

// Restore previous results on index.html if user refreshes or reloads
function restorePreviousResultsIfAny() {
    const path = window.location.pathname.toLowerCase();
    if (path.endsWith('shortlist.html') || path.endsWith('compare.html') || path.endsWith('history.html') || path.endsWith('login.html') || path.endsWith('register.html')) {
        return;
    }

    const stored = localStorage.getItem('current_query') || sessionStorage.getItem('current_query');
    if (!stored) return;

    try {
        const queryData = JSON.parse(stored);
        if (queryData && queryData.raw_query_text) {
            currentQueryData = queryData;
            const textarea = document.getElementById('query-input');
            if (textarea && !textarea.value) {
                textarea.value = queryData.raw_query_text;
            }
            if (queryData.category) {
                selectCategory(queryData.category);
            }
            renderInlineResults(queryData);
        }
    } catch (e) {
        console.error('Failed to restore previous query:', e);
    }
}

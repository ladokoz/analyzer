let token = localStorage.getItem('yt_analyzer_token') || null;

const els = {
    loginOverlay: document.getElementById('loginOverlay'),
    mainApp: document.getElementById('mainApp'),
    settingsModal: document.getElementById('settingsModal'),
    userInput: document.getElementById('usernameInput'),
    passInput: document.getElementById('passwordInput'),
    loginBtn: document.getElementById('loginBtn'),
    loginError: document.getElementById('loginError'),
    
    urlInput: document.getElementById('urlInput'),
    startBtn: document.getElementById('startBtn'),
    stopBtn: document.getElementById('stopBtn'),
    loadSamplesBtn: document.getElementById('loadSamplesBtn'),
    queueStatus: document.getElementById('queueStatus'),
    resultsBody: document.getElementById('resultsBody'),
    downloadCsvBtn: document.getElementById('downloadCsvBtn'),
    
    viewLogsBtn: document.getElementById('viewLogsBtn'),
    clearLogsBtn: document.getElementById('clearLogsBtn'),
    csvsModal: document.getElementById('csvsModal'),
    closeCsvsBtn: document.getElementById('closeCsvsBtn'),
    clearCsvsBtn: document.getElementById('clearCsvsBtn'),
    csvListContainer: document.getElementById('csvListContainer'),
    videosModal: document.getElementById('videosModal'),
    openVideosBtn: document.getElementById('openVideosBtn'),
    closeVideosBtn: document.getElementById('closeVideosBtn'),
    clearVideosBtn: document.getElementById('clearVideosBtn'),
    videosListContainer: document.getElementById('videosListContainer'),
    openSettings: document.getElementById('openSettingsBtn'),
    closeSettings: document.getElementById('closeSettingsBtn'),
    saveSettings: document.getElementById('saveSettingsBtn'),
    modelInp: document.getElementById('modelSelect'),
    inputCostInp: document.getElementById('inputCost'),
    outputCostInp: document.getElementById('outputCost'),
    keepDownloaded: document.getElementById('keepDownloadedVideos'),
    
    promptSelect: document.getElementById('promptSelect'),
    addPromptBtn: document.getElementById('addPromptBtn'),
    delPromptBtn: document.getElementById('delPromptBtn'),
    promptName: document.getElementById('promptName'),
    promptInput: document.getElementById('promptInput'),
    
    appVersionDisplay: document.getElementById('appVersionDisplay'),
    updateAppBtn: document.getElementById('updateAppBtn')
};

function authHeaders() { return { 'Content-Type': 'application/json', 'Authorization': `Bearer ${token}` }; }

if (token) { showApp(); loadSettings(); }

els.loginBtn.addEventListener('click', async () => {
    els.loginBtn.innerText = 'Logging in...';
    try {
        const res = await fetch('/api/login', {
            method: 'POST', headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username: els.userInput.value.trim(), password: els.passInput.value })
        });
        if(res.ok) {
            token = (await res.json()).token;
            localStorage.setItem('yt_analyzer_token', token);
            showApp(); loadSettings();
        } else els.loginError.innerText = 'Invalid credentials.';
    } catch(err) { els.loginError.innerText = 'Server error.'; }
    els.loginBtn.innerText = 'Login';
});

function showApp() { 
    els.loginOverlay.style.display = 'none'; 
    els.mainApp.style.display = 'flex'; 
    if (token && els.viewLogsBtn) els.viewLogsBtn.href = `/api/logs?token=${token}`;
}


// -- PROMPT LOGIC --
let activePrompts = [];
let activePromptId = "default";



function renderPromptDropdown() {
    els.promptSelect.innerHTML = activePrompts.map(p => `<option value="${p.id}">${p.name}</option>`).join('');
    els.promptSelect.value = activePromptId;
    updatePromptFields();
}

function updatePromptFields() {
    const p = activePrompts.find(x => x.id === activePromptId);
    if(p) {
        els.promptName.value = p.name;
        els.promptInput.value = p.text;
    }
}

els.promptSelect.addEventListener('change', () => {
    const oldP = activePrompts.find(x => x.id === activePromptId);
    if(oldP) { oldP.name = els.promptName.value; oldP.text = els.promptInput.value; }
    activePromptId = els.promptSelect.value;
    updatePromptFields();
});

els.promptName.addEventListener('input', () => {
    const p = activePrompts.find(x => x.id === activePromptId);
    if(p) { p.name = els.promptName.value; els.promptSelect.options[els.promptSelect.selectedIndex].text = p.name; }
});
els.promptInput.addEventListener('input', () => {
    const p = activePrompts.find(x => x.id === activePromptId);
    if(p) p.text = els.promptInput.value;
});

els.addPromptBtn.addEventListener('click', () => {
    const newId = "p_" + Date.now();
    activePrompts.push({ id: newId, name: els.promptName.value + " (Copy)", text: els.promptInput.value });
    activePromptId = newId;
    renderPromptDropdown();
});

els.delPromptBtn.addEventListener('click', () => {
    if(activePrompts.length <= 1) return alert("Must have at least one prompt!");
    activePrompts = activePrompts.filter(x => x.id !== activePromptId);
    activePromptId = activePrompts[0].id;
    renderPromptDropdown();
});

// -- SETTINGS FETCHING --
async function loadSettings() {
    try {
        const res = await fetch('/api/settings', { headers: authHeaders() });
        if(res.status === 401) { token = null; localStorage.removeItem('yt_analyzer_token'); location.reload(); return; }
        const set = await res.json();
        
        els.modelInp.value = set.model;
        els.inputCostInp.value = set.input_cost_per_m;
        els.outputCostInp.value = set.output_cost_per_m;
        els.keepDownloaded.checked = set.keep_downloaded_videos || false;

        activePrompts = set.prompts && set.prompts.length ? set.prompts : [{id:"default", name:"Default", text:"Analyze"}];
        activePromptId = set.active_prompt_id || activePrompts[0].id;
        renderPromptDropdown();
        
        try {
            const verRes = await fetch('/api/version', { headers: authHeaders() });
            if (verRes.ok) {
                const verData = await verRes.json();
                if (els.appVersionDisplay) els.appVersionDisplay.innerText = verData.version || '?.?.?';
            }
        } catch(e) {}
        
    } catch(err) { console.error(err); }
}

if (els.updateAppBtn) {
    els.updateAppBtn.addEventListener('click', async () => {
        if (els.updateAppBtn.innerText === "Update Now") {
            els.updateAppBtn.innerText = "Updating...";
            els.updateAppBtn.disabled = true;
            try {
                const res = await fetch('/api/update', { method: 'POST', headers: authHeaders() });
                const data = await res.json();
                if (data.status === 'success') {
                    alert("Update successful! Please restart your terminal/server to apply backend changes. Frontend changes apply immediately.");
                    location.reload();
                } else {
                    alert("Update failed: " + data.message);
                }
            } catch(e) {
                alert("Update failed: " + e.message);
            }
            els.updateAppBtn.innerText = "Check Updates";
            els.updateAppBtn.disabled = false;
        } else {
            els.updateAppBtn.innerText = "Checking...";
            els.updateAppBtn.disabled = true;
            try {
                const res = await fetch('/api/check_update', { method: 'POST', headers: authHeaders() });
                if (res.ok) {
                    const data = await res.json();
                    if (data.update_available) {
                        els.updateAppBtn.innerText = "Update Now";
                        els.updateAppBtn.style.backgroundColor = "var(--danger)";
                        els.updateAppBtn.style.borderColor = "var(--danger)";
                    } else {
                        els.updateAppBtn.innerText = "Up to date!";
                        setTimeout(() => { els.updateAppBtn.innerText = "Check Updates"; }, 3000);
                    }
                } else {
                    els.updateAppBtn.innerText = "Check Updates";
                }
            } catch(e) {
                els.updateAppBtn.innerText = "Check Updates";
            }
            els.updateAppBtn.disabled = false;
        }
    });
}

const MODEL_PRICING = {
    'Gemini 2.0 Flash-Lite': { in: 0.075, out: 0.30 },
    'Gemini 2.0 Flash': { in: 0.10, out: 0.40 },
    'Gemini 2.5 Flash-Lite': { in: 0.10, out: 0.40 },
    'Gemini 2.5 Flash': { in: 0.30, out: 2.50 },
    'Gemini 2.5 Pro (≤ 200K context)': { in: 1.25, out: 10.00 },
    'Gemini 2.5 Pro (> 200K context)': { in: 2.50, out: 15.00 },
    'Gemini 3 Flash Preview': { in: 0.50, out: 3.00 },
    'Gemini 3 Pro Preview (≤ 200K context)': { in: 2.00, out: 12.00 },
    'Gemini 3 Pro Preview (> 200K context)': { in: 4.00, out: 18.00 },
    'Gemini 3.1 Flash Lite Preview': { in: 0.25, out: 1.50 },
    'Gemini 3.1 Pro Preview (≤ 200K context)': { in: 2.00, out: 12.00 },
    'Gemini 3.1 Pro Preview (> 200K context)': { in: 4.00, out: 18.00 }
};

els.modelInp.addEventListener('change', () => {
    const selectedText = els.modelInp.options[els.modelInp.selectedIndex]?.text;
    if(selectedText && MODEL_PRICING[selectedText]) {
        els.inputCostInp.value = MODEL_PRICING[selectedText].in;
        els.outputCostInp.value = MODEL_PRICING[selectedText].out;
    }
});

els.openSettings.addEventListener('click', () => { els.settingsModal.style.display = 'flex'; loadSettings(); });
els.closeSettings.addEventListener('click', () => els.settingsModal.style.display = 'none');
els.saveSettings.addEventListener('click', async () => {
    const p = activePrompts.find(x => x.id === activePromptId);
    if(p) { p.name = els.promptName.value; p.text = els.promptInput.value; }

    els.saveSettings.innerText = 'Saving...';
    try {
        await fetch('/api/settings', {
            method: 'POST', headers: authHeaders(),
            body: JSON.stringify({
                model: els.modelInp.value.trim(),
                input_cost_per_m: parseFloat(els.inputCostInp.value) || 0,
                output_cost_per_m: parseFloat(els.outputCostInp.value) || 0,
                keep_downloaded_videos: els.keepDownloaded.checked,
                prompts: activePrompts,
                active_prompt_id: activePromptId
            })
        });
        els.settingsModal.style.display = 'none';
    } catch (err) {}
    els.saveSettings.innerText = 'Save Changes';
    loadSettings();
});

// -- QUEUE EXECUTION --
let queue = [];
let isAnalyzing = false;
let tableRows = {}; 

if (els.loadSamplesBtn) {
    els.loadSamplesBtn.addEventListener('click', () => {
        els.urlInput.value = `816 308542567
830 9z4NF166ze8
817 440460140
831 9mbHodYmgSI
818 371246774
838 r363IY3mPjc
820 316874134
840 cBubYbtAFiw`;
    });
}

if (els.closeCsvsBtn) {
    els.closeCsvsBtn.addEventListener('click', () => els.csvsModal.style.display = 'none');
}
if (els.closeVideosBtn) {
    els.closeVideosBtn.addEventListener('click', () => els.videosModal.style.display = 'none');
}

async function fetchCSVs() {
    els.csvListContainer.innerHTML = '<p>Loading CSVs...</p>';
    try {
        const res = await fetch('/api/csvs', { headers: authHeaders() });
        if(!res.ok) throw new Error("Failed to load list");
        const data = await res.json();
        if(data.files && data.files.length > 0) {
            els.csvListContainer.innerHTML = data.files.map(f => `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <div>
                        <strong style="color: var(--accent);">${f.name}</strong><br>
                        <small style="color: var(--text-sec)">${new Date(f.modified * 1000).toLocaleString()} - ${(f.size / 1024).toFixed(1)} KB</small>
                    </div>
                    <div>
                        <button onclick="deleteCsv('${f.name}')" class="btn-secondary" style="width: auto; padding: 0.4rem 0.6rem; margin-right: 0.5rem; font-size: 0.85rem;" title="Delete">🗑️</button>
                        <a href="/api/csvs/${f.name}?token=${token}" target="_blank" class="btn-primary" style="text-decoration:none; padding: 0.4rem 0.8rem; width: auto; font-size: 0.85rem;">Download</a>
                    </div>
                </div>
            `).join('');
        } else {
            els.csvListContainer.innerHTML = '<p>No CSV files found yet.</p>';
        }
    } catch (e) {
        els.csvListContainer.innerHTML = '<p class="error-msg">Failed to load CSVs.</p>';
    }
}

els.downloadCsvBtn.addEventListener('click', async () => {
    els.csvsModal.style.display = 'flex';
    await fetchCSVs();
});

window.deleteCsv = async function(filename) {
    if(!confirm(`Delete ${filename}?`)) return;
    try {
        await fetch(`/api/csvs/${filename}`, { method: 'DELETE', headers: authHeaders() });
        await fetchCSVs();
    } catch(e) {}
};

if(els.clearCsvsBtn) {
    els.clearCsvsBtn.addEventListener('click', async () => {
        if(!confirm('Delete ALL CSVs? This cannot be undone.')) return;
        try {
            await fetch('/api/csvs', { method: 'DELETE', headers: authHeaders() });
            await fetchCSVs();
        } catch(e) {}
    });
}

async function fetchVideos() {
    els.videosListContainer.innerHTML = '<p>Loading Videos...</p>';
    try {
        const res = await fetch('/api/videos', { headers: authHeaders() });
        if(!res.ok) throw new Error("Failed to load list");
        const data = await res.json();
        if(data.files && data.files.length > 0) {
            els.videosListContainer.innerHTML = data.files.map(f => `
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; padding: 0.75rem; background: rgba(255,255,255,0.05); border-radius: 6px;">
                    <div>
                        <strong style="color: var(--accent);">${f.name}</strong><br>
                        <small style="color: var(--text-sec)">${new Date(f.modified * 1000).toLocaleString()} - ${(f.size / (1024*1024)).toFixed(2)} MB</small>
                    </div>
                    <div>
                        <button onclick="deleteVideo('${f.name}')" class="btn-secondary" style="width: auto; padding: 0.4rem 0.6rem; margin-right: 0.5rem; font-size: 0.85rem;" title="Delete">🗑️</button>
                        <a href="/api/videos/${f.name}?token=${token}" target="_blank" class="btn-primary" style="text-decoration:none; padding: 0.4rem 0.8rem; width: auto; font-size: 0.85rem;">Download</a>
                    </div>
                </div>
            `).join('');
        } else {
            els.videosListContainer.innerHTML = '<p>No Kept Videos found yet.</p>';
        }
    } catch (e) {
        els.videosListContainer.innerHTML = '<p class="error-msg">Failed to load Videos.</p>';
    }
}

if(els.openVideosBtn) {
    els.openVideosBtn.addEventListener('click', async () => {
        els.videosModal.style.display = 'flex';
        await fetchVideos();
    });
}

window.deleteVideo = async function(filename) {
    if(!confirm(`Delete ${filename}?`)) return;
    try {
        await fetch(`/api/videos/${filename}`, { method: 'DELETE', headers: authHeaders() });
        await fetchVideos();
    } catch(e) {}
};

if(els.clearVideosBtn) {
    els.clearVideosBtn.addEventListener('click', async () => {
        if(!confirm('Delete ALL Videos? This cannot be undone.')) return;
        try {
            await fetch('/api/videos', { method: 'DELETE', headers: authHeaders() });
            await fetchVideos();
        } catch(e) {}
    });
}

if(els.clearLogsBtn) {
    els.clearLogsBtn.addEventListener('click', async () => {
        if(!confirm('Clear application logs?')) return;
        try {
            await fetch('/api/logs', { method: 'DELETE', headers: authHeaders() });
            alert("Logs cleared successfully.");
        } catch(e) {}
    });
}

els.startBtn.addEventListener('click', async () => {
    const rawLines = els.urlInput.value.split('\n');
    let addedUrls = [];
    
    const now = new Date();
    const batchId = `${now.getFullYear()}${(now.getMonth()+1).toString().padStart(2, '0')}${now.getDate().toString().padStart(2, '0')}_${now.getHours().toString().padStart(2, '0')}${now.getMinutes().toString().padStart(2, '0')}${now.getSeconds().toString().padStart(2, '0')}`;
    
    for (const line of rawLines) {
        let raw = line.trim();
        if(!raw) continue;

        let internalId = '';
        let link = raw;

        const parts = raw.split(/\s+/);
        if (parts.length >= 2) {
            link = parts.pop();
            internalId = parts.join(' ');
        }
        
        if (!link.startsWith('http')) {
            if (/^\d{6,15}$/.test(link)) {
                link = 'https://vimeo.com/' + link;
            } else if (/^[A-Za-z0-9_-]{11}$/.test(link)) {
                link = 'https://www.youtube.com/watch?v=' + link;
            }
        }

        if(link.includes('youtube.com') || link.includes('youtu.be') || link.includes('vimeo.com')) {
            addedUrls.push({url: link, id: internalId, batch_id: batchId});
        }
    }
    
    if(addedUrls.length > 0) {
        els.urlInput.value = '';
        for (const task of addedUrls) {
            try {
                await fetch('/api/analyze', {
                    method: 'POST', headers: authHeaders(),
                    body: JSON.stringify({url: task.url, internal_id: task.id, batch_id: task.batch_id})
                });
            } catch(e) { console.error("Submit error", e); }
        }
        pollJobs();
    } else alert("Please enter valid YouTube or Vimeo URLs.");
});

function getStatusClass(status) {
    status = status || "Pending";
    if(status === "Pending") return "pending";
    if(status === "Done") return "done";
    if(status === "Error" || status.includes("Canceled") || status.includes("Done-Warning")) return "error";
    return "analyzing";
}

async function pollJobs() {
    if(!token) return;
    try {
        const res = await fetch('/api/jobs', { headers: authHeaders() });
        if (!res.ok) return;
        const data = await res.json();
        const jobs = data.jobs || {};
        
        let pending = 0;
        let analyzing = 0;
        
        for (const [url, job] of Object.entries(jobs)) {
            if (job.status === "Pending") pending++;
            else if (job.status && (job.status.includes("...") || job.status.includes("Starting"))) analyzing++;
            
            if (!tableRows[url]) {
                const tr = document.createElement('tr');
                tr.innerHTML = `
                    <td class="res-status"></td>
                    <td class="res-internalid" style="color: var(--text-sec); font-size: 0.85rem;"></td>
                    <td class="res-time" style="color: var(--text-sec); font-size: 0.8rem;"></td>
                    <td class="res-title" style="font-weight: 500;"></td>
                    <td><a href="" class="res-link" target="_blank" style="color:var(--accent)"></a></td>
                    <td class="res-tags"></td>
                    <td class="res-genres"></td>
                    <td class="res-anim"></td>
                    <td class="res-acc"></td>
                    <td class="res-dirs"></td>
                    <td class="res-prods"></td>
                    <td class="res-year"></td>
                    <td class="res-pcomp"></td>
                    <td class="res-school"></td>
                    <td class="res-dist"></td>
                    <td class="res-animators"></td>
                    <td class="res-script"></td>
                    <td class="res-music"></td>
                    <td class="res-sound"></td>
                    <td class="res-editors"></td>
                    <td class="res-festivals"></td>
                    <td class="res-awards"></td>
                    <td class="res-tokens" style="color: var(--text-sec); font-size: 0.85rem;"></td>
                    <td class="res-cost" style="color: var(--success); font-weight: 500;"></td>
                `;
                els.resultsBody.append(tr);
                tableRows[url] = tr;
            }
            
            const tr = tableRows[url];
            tr.querySelector('.res-internalid').innerText = job.internal_id || '-';
            tr.querySelector('.res-time').innerText = job.timestamp || '-';
            tr.querySelector('.res-title').innerText = job.title || '-';
            tr.querySelector('.res-link').href = url;
            tr.querySelector('.res-link').innerText = url.substring(0,25) + '...';
            
            const resData = job.result ? (job.result.data || job.result) : null;
            if (resData) {
                const jStr = (field) => resData[field] ? resData[field].join(', ') : 'None';
                tr.querySelector('.res-tags').innerText = jStr('tags');
                tr.querySelector('.res-genres').innerText = jStr('genres');
                tr.querySelector('.res-anim').innerText = jStr('animation_techniques');
                tr.querySelector('.res-acc').innerText = resData.accessibility_rating || 'N/A';
                tr.querySelector('.res-dirs').innerText = jStr('film_directors');
                tr.querySelector('.res-prods').innerText = jStr('film_producers');
                tr.querySelector('.res-year').innerText = resData.year || 'N/A';
                tr.querySelector('.res-pcomp').innerText = jStr('production_companies');
                tr.querySelector('.res-school').innerText = jStr('school_or_university');
                tr.querySelector('.res-dist').innerText = jStr('distribution_and_sales_companies');
                tr.querySelector('.res-animators').innerText = jStr('animators');
                tr.querySelector('.res-script').innerText = jStr('script_writers');
                tr.querySelector('.res-music').innerText = jStr('music_composers');
                tr.querySelector('.res-sound').innerText = jStr('sound_designers');
                tr.querySelector('.res-editors').innerText = jStr('editors');
                tr.querySelector('.res-festivals').innerText = jStr('festival_selection');
                tr.querySelector('.res-awards').innerText = jStr('awards');
            } else {
                tr.querySelector('.res-tags').innerText = '-';
                tr.querySelector('.res-genres').innerText = '-';
                tr.querySelector('.res-anim').innerText = '-';
                tr.querySelector('.res-acc').innerText = '-';
                tr.querySelector('.res-dirs').innerText = '-';
                tr.querySelector('.res-prods').innerText = '-';
                tr.querySelector('.res-year').innerText = '-';
                tr.querySelector('.res-pcomp').innerText = '-';
                tr.querySelector('.res-school').innerText = '-';
                tr.querySelector('.res-dist').innerText = '-';
                tr.querySelector('.res-animators').innerText = '-';
                tr.querySelector('.res-script').innerText = '-';
                tr.querySelector('.res-music').innerText = '-';
                tr.querySelector('.res-sound').innerText = '-';
                tr.querySelector('.res-editors').innerText = '-';
                tr.querySelector('.res-festivals').innerText = '-';
                tr.querySelector('.res-awards').innerText = '-';
            }
            
            tr.querySelector('.res-tokens').innerText = job.tokens ? job.tokens.toLocaleString() : '-';
            tr.querySelector('.res-cost').innerText = job.cost ? '$' + job.cost.toFixed(4) : '-';
            
            let statusText = job.status;
            if(job.error) statusText = `Error: ${job.error}`;
            tr.querySelector('.res-status').innerHTML = `<span class="status ${getStatusClass(job.status)}" title="${job.error || ''}">${statusText}</span>`;
        }
        
        if (analyzing > 0 || pending > 0) {
            els.queueStatus.innerText = `Analyzing... (${pending} pending, ${analyzing} active)`;
        } else {
            els.queueStatus.innerText = 'Idle';
        }
    } catch(e) {}
}

if(els.stopBtn) {
    els.stopBtn.addEventListener('click', async () => {
        if(!confirm("Are you sure you want to stop all tasks?")) return;
        try {
            await fetch('/api/stop', { method: 'POST', headers: authHeaders() });
            pollJobs();
        } catch(e) { console.error(e) }
    });
}

// Start polling immediately to restore state
setInterval(pollJobs, 2000);
if(token) pollJobs();

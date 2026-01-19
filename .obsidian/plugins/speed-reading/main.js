"use strict";
Object.defineProperty(exports, "__esModule", { value: true });
const obsidian_1 = require("obsidian");
const DEFAULT_SETTINGS = {
    defaultWPM: 300,
    showProgressBar: true,
};
/**
 * RSVP Modal for Speed Reading
 */
class SpeedReadModal extends obsidian_1.Modal {
    constructor(app, text, defaultWPM, showProgressBar, onWPMChange) {
        super(app);
        this.onWPMChange = onWPMChange;
        this.currentIndex = 0;
        this.intervalId = null;
        this.isRunning = false;
        // For global spacebar handler
        this.globalSpaceHandler = null;
        // Clean/strip Markdown for RSVP display
        this.words = SpeedReadModal.tokenizeText(SpeedReadModal.stripMarkdown(text));
        this.wpm = defaultWPM;
        this.showProgressBar = showProgressBar;
    }
    onOpen() {
        const { contentEl } = this;
        // Modal container
        contentEl.empty();
        contentEl.addClass("speed-read-modal");
        // Add mobile class if running on Obsidian Mobile
        if (this.app.isMobile) {
            contentEl.addClass("mobile");
        }
        // RSVP display area
        this.displayEl = contentEl.createDiv({ cls: "rsvp-display" });
        this.displayEl.setAttr("tabindex", "0");
        this.renderCurrentWord();
        // Mouse wheel to move progress back/forward (attach to modal container for reliability)
        // Attach wheel event to RSVP display area, now focusable
        this.displayEl.addEventListener("wheel", (e) => {
            e.preventDefault();
            if (this.isRunning) {
                this.stop();
            }
            if (e.deltaY < 0) {
                this.showPreviousWord();
            }
            else if (e.deltaY > 0) {
                this.showNextWord();
            }
        }, { passive: false });
        // Keyboard navigation: left/right or up/down arrows to move between words (debounced)
        let lastNavTime = 0;
        this.displayEl.addEventListener("keydown", (e) => {
            const now = Date.now();
            if (now - lastNavTime < 100)
                return; // debounce: 100ms
            lastNavTime = now;
            if (this.isRunning)
                this.stop(); // Always pause RSVP before manual navigation
            if (e.key === "ArrowLeft" || e.key === "ArrowUp") {
                e.preventDefault();
                this.showPreviousWord();
            }
            else if (e.key === "ArrowRight" || e.key === "ArrowDown") {
                e.preventDefault();
                this.showNextWord();
            }
        });
        // Global spacebar handler for pause/start
        this.globalSpaceHandler = (e) => {
            // Only trigger if modal is open and no input/button/textarea is focused
            if ((e.key === " " || e.code === "Space" || e.keyCode === 32) &&
                document.activeElement &&
                !(document.activeElement instanceof HTMLInputElement) &&
                !(document.activeElement instanceof HTMLTextAreaElement) &&
                !(document.activeElement instanceof HTMLButtonElement)) {
                e.preventDefault();
                e.stopPropagation();
                this.toggle();
                // Always refocus the RSVP display area so keyboard navigation works after toggling
                if (this.displayEl) {
                    this.displayEl.focus();
                }
            }
        };
        window.addEventListener("keydown", this.globalSpaceHandler, true);
        // Focus the display area so it can receive keyboard events
        this.displayEl.focus();
        // Progress bar
        if (this.showProgressBar) {
            this.progressBar = contentEl.createDiv({ cls: "rsvp-progress-bar" });
            this.updateProgressBar();
        }
        // Controls container
        const controls = contentEl.createDiv({ cls: "rsvp-controls" });
        // Start/Pause button
        this.startPauseBtn = controls.createEl("button", { text: "Start" });
        this.startPauseBtn.onclick = () => this.toggle();
        // WPM control
        controls.createSpan({ text: " WPM: " });
        this.wpmInput = controls.createEl("input");
        this.wpmInput.type = "number";
        this.wpmInput.value = this.wpm.toString();
        this.wpmInput.min = "50";
        this.wpmInput.max = "2000";
        this.wpmInput.style.width = "60px";
        this.wpmInput.onchange = () => {
            const val = parseInt(this.wpmInput.value, 10);
            if (!isNaN(val) && val > 0) {
                this.wpm = val;
                if (this.onWPMChange) {
                    this.onWPMChange(val);
                }
                if (this.isRunning) {
                    this.stop();
                    this.start();
                }
            }
        };
        // Close button (standard modal close)
        const closeBtn = controls.createEl("button", { text: "Close" });
        closeBtn.onclick = () => this.close();
    }
    onClose() {
        // Remove global spacebar handler if present
        if (this.globalSpaceHandler) {
            window.removeEventListener("keydown", this.globalSpaceHandler, true);
            this.globalSpaceHandler = null;
        }
        this.stop();
        this.contentEl.empty();
    }
    toggle() {
        if (this.isRunning) {
            this.stop();
        }
        else {
            this.start();
        }
    }
    start() {
        if (this.isRunning)
            return;
        this.isRunning = true;
        this.startPauseBtn.textContent = "Pause";
        this.intervalId = window.setInterval(() => {
            this.showNextWord();
        }, 60000 / this.wpm);
    }
    stop() {
        this.isRunning = false;
        this.startPauseBtn.textContent = "Start";
        if (this.intervalId !== null) {
            clearInterval(this.intervalId);
            this.intervalId = null;
        }
    }
    renderCurrentWord() {
        const word = this.words[this.currentIndex] || "";
        const pivotIdx = SpeedReadModal.getPivotIndex(word);
        // Pad left and right with invisible monospace spans so the pivot char is always at PIVOT_POS
        const leftPad = SpeedReadModal.PIVOT_POS - pivotIdx;
        const rightPad = Math.max(0, SpeedReadModal.DISPLAY_CHARS - (leftPad + word.length));
        let html = "";
        for (let i = 0; i < leftPad; i++) {
            html += `<span class="rsvp-invisible-word">m</span>`;
        }
        for (let i = 0; i < word.length; i++) {
            if (i === pivotIdx) {
                html += `<span class="rsvp-pivot-char">${word[i]}</span>`;
            }
            else {
                html += `<span class="rsvp-focus-word">${word[i]}</span>`;
            }
        }
        for (let i = 0; i < rightPad; i++) {
            html += `<span class="rsvp-invisible-word">m</span>`;
        }
        this.displayEl.innerHTML = html;
    }
    showNextWord() {
        if (this.currentIndex < this.words.length - 1) {
            this.currentIndex++;
            this.renderCurrentWord();
            this.updateProgressBar();
        }
        // Do nothing if at the last word
    }
    showPreviousWord() {
        if (this.currentIndex > 0) {
            this.currentIndex--;
            this.renderCurrentWord();
            this.updateProgressBar();
        }
        // Do nothing if at the first word
    }
    updateProgressBar() {
        if (!this.showProgressBar || !this.progressBar)
            return;
        const percent = Math.min(100, ((this.currentIndex + 1) / this.words.length) * 100);
        this.progressBar.style.width = "100%";
        this.progressBar.style.height = "8px";
        this.progressBar.style.background = "#444";
        this.progressBar.style.borderRadius = "4px";
        this.progressBar.style.marginBottom = "1em";
        this.progressBar.innerHTML = `<div style="height:100%;width:${percent}%;background:#4f8cff;border-radius:4px;"></div>`;
    }
    // Spritz-like pivot index calculation
    static getPivotIndex(word) {
        if (word.length <= 1)
            return 0;
        if (word.length <= 5)
            return 1;
        if (word.length <= 9)
            return 2;
        return 3;
    }
    // Remove Markdown formatting for RSVP display
    static stripMarkdown(text) {
        // Remove code blocks, inline code, bold, italics, links, images, headings, blockquotes, lists, etc.
        return text
            .replace(/`{3}[\s\S]*?`{3}/g, "") // code blocks
            .replace(/`[^`]*`/g, "") // inline code
            .replace(/!\[.*?\]\(.*?\)/g, "") // images
            .replace(/\[([^\]]+)\]\([^)]+\)/g, "$1") // links
            .replace(/[*_~`>#-]/g, "") // *, _, ~, `, >, #, -
            .replace(/^\s*\d+\.\s+/gm, "") // numbered lists
            .replace(/^\s*[-*+]\s+/gm, "") // bullet lists
            .replace(/^\s*>+\s?/gm, "") // blockquotes
            .replace(/#+\s/g, "") // headings
            .replace(/\n{2,}/g, "\n") // multiple newlines
            .replace(/\r/g, "")
            .trim();
    }
    // Tokenize text into words, handling punctuation and whitespace
    static tokenizeText(text) {
        return text
            .replace(/\s+/g, " ")
            .split(" ")
            .filter((w) => w.length > 0);
    }
}
// Pivot position (number of monospace chars from left edge)
SpeedReadModal.DISPLAY_CHARS = 20; // Use more space for long words
SpeedReadModal.PIVOT_POS = 10; // Centered in 20-char display
/** Settings tab for the plugin */
class SpeedReadingSettingTab extends obsidian_1.PluginSettingTab {
    constructor(app, plugin) {
        super(app, plugin);
        this.plugin = plugin;
    }
    display() {
        const { containerEl } = this;
        containerEl.empty();
        containerEl.createEl("h2", { text: "Speed Reading Settings" });
        new obsidian_1.Setting(containerEl)
            .setName("Default WPM")
            .setDesc("Set the default words per minute for speed reading.")
            .addText((text) => text
            .setPlaceholder("300")
            .setValue(this.plugin.settings.defaultWPM.toString())
            .onChange(async (value) => {
            const num = parseInt(value, 10);
            if (!isNaN(num) && num > 0) {
                this.plugin.settings.defaultWPM = num;
                await this.plugin.saveSettings();
            }
        }));
        // Progress Bar toggle
        new obsidian_1.Setting(containerEl)
            .setName("Show Progress Bar")
            .setDesc("Show a progress bar in the RSVP modal.")
            .addToggle((toggle) => toggle
            .setValue(this.plugin.settings.showProgressBar)
            .onChange(async (value) => {
            this.plugin.settings.showProgressBar = value;
            await this.plugin.saveSettings();
        }));
    }
}
class SpeedReadingPlugin extends obsidian_1.Plugin {
    constructor() {
        super(...arguments);
        this.currentModal = null;
    }
    async onload() {
        await this.loadSettings();
        this.addCommand({
            id: "speed-read-selected-text",
            name: "Speed Read Selected Text",
            editorCallback: (editor) => {
                const selectedText = editor.getSelection();
                if (!selectedText || selectedText.trim() === "") {
                    new obsidian_1.Notice("Please select text to speed read.");
                    return;
                }
                // Ensure only one modal is open at a time
                if (this.currentModal) {
                    this.currentModal.close();
                }
                this.currentModal = new SpeedReadModal(this.app, selectedText, this.settings.defaultWPM, this.settings.showProgressBar, async (wpm) => {
                    this.settings.defaultWPM = wpm;
                    await this.saveSettings();
                });
                this.currentModal.open();
            },
        });
        this.addSettingTab(new SpeedReadingSettingTab(this.app, this));
    }
    async loadSettings() {
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    }
    async saveSettings() {
        await this.saveData(this.settings);
    }
    onunload() {
        // Cleanup if needed
        if (this.currentModal) {
            this.currentModal.close();
            this.currentModal = null;
        }
    }
}
exports.default = SpeedReadingPlugin;

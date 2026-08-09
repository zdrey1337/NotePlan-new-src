const API_BASE = "https://noteplan-new-src.onrender.com/"

const state = {
    status: "all",
    subject: "all",
    query: ""
};

const $ = selector => document.querySelector(selector);

const grid = $("#notesGrid");
const empty = $("#emptyState");
const modal = $("#noteModal");
const form = $("#noteForm");

let currentUser = null;

async function api(url, options = {}) {
    const response = await fetch(
        `${API_BASE}${url}`,
        {
            headers: {
                "Content-Type": "application/json"
            },
            credentials: "include",
            ...options
        }
    );

    const data = await response.json();

    if (!response.ok) {
        throw new Error(
            data.error || "Request failed."
        );
    }

    return data;
}

function escapeHtml(value = "") {
    return String(value).replace(
        /[&<>"']/g,
        character => ({
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': "&quot;",
            "'": "&#039;"
        }[character])
    );
}

function getFirstName(fullName = "") {
    return fullName.trim().split(/\s+/)[0] || "Student";
}

function getInitials(fullName = "") {
    const parts = fullName.trim().split(/\s+/).filter(Boolean);

    if (!parts.length) {
        return "--";
    }

    if (parts.length === 1) {
        return parts[0].slice(0, 2).toUpperCase();
    }

    return (
        parts[0][0] +
        parts[parts.length - 1][0]
    ).toUpperCase();
}

function getGreeting() {
    const hour = new Date().getHours();

    if (hour >= 5 && hour < 12) {
        return "Good Morning";
    }

    if (hour >= 12 && hour < 18) {
        return "Good Afternoon";
    }

    return "Good Evening";
}

function updateUserInterface(user) {
    if (!user) {
        return;
    }

    currentUser = user;

    const firstName = getFirstName(
        user.full_name
    );

    const initials = getInitials(
        user.full_name
    );

    const greeting = getGreeting();

    const profileName =
        document.getElementById("profileName");

    const sidebarName =
        document.getElementById(
            "sidebarProfileName"
        );

    const sidebarInfo =
        document.getElementById(
            "sidebarProfileInfo"
        );

    const sidebarAvatar =
        document.getElementById(
            "sidebarAvatar"
        );

    const topAvatar =
        document.getElementById(
            "topAvatar"
        );

    const welcomeMessage =
        document.getElementById(
            "welcomeMessage"
        );

    const welcomeSection =
        document.getElementById(
            "welcomeSection"
        );

    if (profileName) {
        profileName.textContent =
            user.full_name;
    }

    if (sidebarName) {
        sidebarName.textContent =
            user.full_name;
    }

    if (sidebarInfo) {
        sidebarInfo.textContent =
            `${user.section} • ST. JAMES`;
    }

    if (sidebarAvatar) {
        sidebarAvatar.textContent =
            initials;
    }

    if (topAvatar) {
        topAvatar.textContent =
            initials;
    }

    if (welcomeMessage) {
        welcomeMessage.textContent =
            `${greeting}, ${firstName} 👋`;
    }

    if (welcomeSection) {
        welcomeSection.textContent =
            `${user.section} • ST. JAMES`;
    }

    document.title =
        `${user.section} • NotePlan`;
}

function showToast(message, error = false) {
    const toast = $("#toast");

    if (!toast) {
        return;
    }

    toast.textContent = message;

    toast.className = `toast show ${
        error ? "error" : ""
    }`;

    setTimeout(() => {
        toast.className = "toast";
    }, 2200);
}

function formatDate(dateValue) {
    if (!dateValue) {
        return "No deadline";
    }

    const date = new Date(dateValue);

    if (Number.isNaN(date.getTime())) {
        return "No deadline";
    }

    return date.toLocaleString([], {
        month: "short",
        day: "numeric",
        hour: "numeric",
        minute: "2-digit"
    });
}

function createNoteCard(note) {
    const title = escapeHtml(note.title);
    const content = escapeHtml(note.content);
    const subject = escapeHtml(note.subject);
    const author = escapeHtml(note.author);

    return `
        <article
            class="note-card ${note.color}-note ${
                note.completed ? "completed-note" : ""
            }"
            data-id="${note.id}">

            <div class="note-top">
                <span class="tag ${note.color}-tag">
                    ${subject}
                </span>

                <div class="note-actions">
                    ${
                        note.pinned
                            ? '<span class="pin">⌖</span>'
                            : ""
                    }

                    ${
                        note.important
                            ? '<span class="star">★</span>'
                            : ""
                    }

                    <button
                        class="menu-btn"
                        data-action="edit">
                        •••
                    </button>
                </div>
            </div>

            <h4>
                ${title}
            </h4>

            <p>
                ${content || "No content added."}
            </p>

            <div class="note-meta">
                <span>
                    👤 ${author}
                </span>

                <span>
                    ${formatDate(note.due_date)}
                </span>
            </div>

            <div class="note-footer">
                <label class="complete-toggle">
                    <input
                        type="checkbox"
                        data-action="complete"
                        ${note.completed ? "checked" : ""}>

                    <span>
                        ${
                            note.completed
                                ? "Completed"
                                : "Mark complete"
                        }
                    </span>
                </label>

                <button
                    class="edit-link"
                    data-action="edit">
                    Edit
                </button>
            </div>
        </article>
    `;
}

async function loadNotes() {
    try {
        const params = new URLSearchParams({
            q: state.query,
            subject: state.subject,
            status: state.status
        });

        const notes = await api(
            `/api/notes?${params.toString()}`
        );

        grid.innerHTML = notes
            .map(createNoteCard)
            .join("");

        empty.classList.toggle(
            "hidden",
            notes.length > 0
        );

        $("#resultCount").textContent =
            `${notes.length} note${
                notes.length === 1 ? "" : "s"
            }`;

    } catch (error) {
        showToast(
            error.message,
            true
        );
    }
}

async function loadStats() {
    try {
        const stats = await api(
            "/api/stats"
        );

        $("#totalStat").textContent =
            stats.total;

        $("#importantStat").textContent =
            stats.important;

        $("#completedStat").textContent =
            stats.completed;

        $("#subjectsStat").textContent =
            stats.subjects;

        $("#dashboardCount").textContent =
            stats.total;

        $("#importantCount").textContent =
            stats.important;

    } catch (error) {
        showToast(
            error.message,
            true
        );
    }
}

async function loadDeadlines() {
    try {
        const notes = await api(
            "/api/notes"
        );

        const upcoming = notes
            .filter(note =>
                note.due_date &&
                !note.completed
            )
            .sort(
                (a, b) =>
                    new Date(a.due_date) -
                    new Date(b.due_date)
            )
            .slice(0, 4);

        $("#deadlineCount").textContent =
            upcoming.length;

        if (!upcoming.length) {
            $("#deadlines").innerHTML = `
                <p class="no-deadlines">
                    No upcoming deadlines.
                </p>
            `;

            return;
        }

        $("#deadlines").innerHTML =
            upcoming.map(note => `
                <div class="deadline">
                    <i class="${note.color}"></i>

                    <div>
                        <b>
                            ${escapeHtml(note.title)}
                        </b>

                        <small>
                            ${formatDate(note.due_date)}
                        </small>
                    </div>
                </div>
            `).join("");

    } catch (error) {
        showToast(
            error.message,
            true
        );
    }
}

async function refresh() {
    await Promise.all([
        loadNotes(),
        loadStats(),
        loadDeadlines()
    ]);
}

function openModal(note = null) {
    modal.classList.remove(
        "hidden"
    );

    $("#modalEyebrow").textContent =
        note ? "EDIT NOTE" : "NEW NOTE";

    $("#modalTitle").textContent =
        note
            ? "Edit sticky note"
            : "Create sticky note";

    $("#noteId").value =
        note?.id || "";

    $("#title").value =
        note?.title || "";

    $("#content").value =
        note?.content || "";

    $("#subject").value =
        note?.subject || "ICT 11-2";

    $("#color").value =
        note?.color || "blue";

    $("#important").checked =
        !!note?.important;

    $("#pinned").checked =
        !!note?.pinned;

    $("#dueDate").value =
        note?.due_date
            ? note.due_date.slice(0, 16)
            : "";

    $("#deleteBtn").classList.toggle(
        "hidden",
        !note
    );

    $("#title").focus();
}

function closeModal() {
    modal.classList.add(
        "hidden"
    );

    form.reset();

    $("#noteId").value = "";
}

async function saveNote(event) {
    event.preventDefault();

    const id = $("#noteId").value;

    const payload = {
        title: $("#title").value.trim(),
        content: $("#content").value.trim(),
        subject: $("#subject").value,
        color: $("#color").value,
        important: $("#important").checked,
        pinned: $("#pinned").checked,
        due_date: $("#dueDate").value || null
    };

    if (!payload.title) {
        showToast(
            "Please enter a title.",
            true
        );

        return;
    }

    try {
        if (id) {
            await api(
                `/api/notes/${id}`,
                {
                    method: "PUT",
                    body: JSON.stringify(payload)
                }
            );

            showToast(
                "Note updated successfully."
            );

        } else {
            await api(
                "/api/notes",
                {
                    method: "POST",
                    body: JSON.stringify(payload)
                }
            );

            showToast(
                "Sticky note created."
            );
        }

        closeModal();

        await refresh();

    } catch (error) {
        showToast(
            error.message,
            true
        );
    }
}

async function deleteCurrentNote() {
    const id = $("#noteId").value;

    if (!id) {
        return;
    }

    const confirmed = confirm(
        "Delete this sticky note permanently?"
    );

    if (!confirmed) {
        return;
    }

    try {
        await api(
            `/api/notes/${id}`,
            {
                method: "DELETE"
            }
        );

        closeModal();

        showToast(
            "Note deleted."
        );

        await refresh();

    } catch (error) {
        showToast(
            error.message,
            true
        );
    }
}

grid.addEventListener(
    "click",
    async event => {
        const action =
            event.target.closest(
                "[data-action]"
            );

        if (!action) {
            return;
        }

        const card =
            action.closest(".note-card");

        if (!card) {
            return;
        }

        const id =
            card.dataset.id;

        if (
            action.dataset.action ===
            "edit"
        ) {
            try {
                const notes =
                    await api(
                        "/api/notes"
                    );

                const note =
                    notes.find(
                        item =>
                            String(item.id) ===
                            String(id)
                    );

                if (note) {
                    openModal(note);
                }

            } catch (error) {
                showToast(
                    error.message,
                    true
                );
            }
        }
    }
);

grid.addEventListener(
    "change",
    async event => {
        if (
            event.target.dataset.action !==
            "complete"
        ) {
            return;
        }

        const card =
            event.target.closest(
                ".note-card"
            );

        const id =
            card.dataset.id;

        try {
            await api(
                `/api/notes/${id}`,
                {
                    method: "PUT",
                    body: JSON.stringify({
                        completed:
                            event.target.checked
                    })
                }
            );

            showToast(
                event.target.checked
                    ? "Note completed."
                    : "Note reopened."
            );

            await refresh();

        } catch (error) {
            showToast(
                error.message,
                true
            );
        }
    }
);

$("#newNoteBtn").addEventListener(
    "click",
    () => openModal()
);

$("#closeModal").addEventListener(
    "click",
    closeModal
);

$("#cancelBtn").addEventListener(
    "click",
    closeModal
);

$("#deleteBtn").addEventListener(
    "click",
    deleteCurrentNote
);

form.addEventListener(
    "submit",
    saveNote
);

$("#searchInput").addEventListener(
    "input",
    event => {
        state.query =
            event.target.value.trim();

        loadNotes();
    }
);

document
    .querySelectorAll(
        "[data-status]"
    )
    .forEach(button => {
        button.addEventListener(
            "click",
            () => {
                state.status =
                    button.dataset.status;

                document
                    .querySelectorAll(
                        ".nav-link, .filter"
                    )
                    .forEach(element => {
                        element.classList.toggle(
                            "active",
                            element.dataset.status ===
                            state.status
                        );
                    });

                loadNotes();
            }
        );
    });

document
    .querySelectorAll(
        "[data-subject]"
    )
    .forEach(button => {
        button.addEventListener(
            "click",
            () => {
                state.subject =
                    button.dataset.subject;

                document
                    .querySelectorAll(
                        ".subject-link"
                    )
                    .forEach(element => {
                        element.classList.toggle(
                            "selected",
                            element.dataset.subject ===
                            state.subject
                        );
                    });

                loadNotes();
            }
        );
    });

document.addEventListener(
    "keydown",
    event => {
        if (
            (event.ctrlKey ||
            event.metaKey) &&
            event.key.toLowerCase() === "k"
        ) {
            event.preventDefault();

            $("#searchInput").focus();
        }

        if (
            event.key === "Escape" &&
            !modal.classList.contains(
                "hidden"
            )
        ) {
            closeModal();
        }
    }
);

modal.addEventListener(
    "click",
    event => {
        if (
            event.target === modal
        ) {
            closeModal();
        }
    }
);

async function checkAuthentication() {
    try {
        
        const response = await fetch(
            `${API_BASE}/api/me`,
            {
                credentials: "include"
            }
        );

        if (!response.ok) {
            window.location.href = "/login/";
            return null;
        }

        const data = await response.json();

        if (!data.authenticated) {
            window.location.href = "/login/";
            return null;
        }

        const user = data.user;

        const profileName = document.getElementById("profileName");
        const sidebarName = document.getElementById("sidebarName");
        const sidebarSection = document.getElementById("sidebarSection");
        const welcomeMessage = document.getElementById("welcomeMessage");

        if (profileName) {
            profileName.textContent = user.full_name;
        }

        if (sidebarName) {
            sidebarName.textContent = user.full_name;
        }

        if (sidebarSection) {
            sidebarSection.textContent =
                `${user.section} • ST. JAMES`;
        }

        const avatarText = user.full_name
            .split(" ")
            .map(name => name[0])
            .slice(0, 2)
            .join("")
            .toUpperCase();

        const profileAvatar =
            document.getElementById("profileAvatar");

        const topAvatar =
            document.getElementById("topAvatar");

        if (profileAvatar) {
            profileAvatar.textContent = avatarText;
        }

        if (topAvatar) {
            topAvatar.textContent = avatarText;
        }

        const hour = new Date().getHours();

        let greeting;

        if (hour >= 5 && hour < 12) {
            greeting = "Good Morning";
        } else if (hour >= 12 && hour < 18) {
            greeting = "Good Afternoon";
        } else {
            greeting = "Good Evening";
        }

        const firstName = user.full_name
            .trim()
            .split(/\s+/)[0];

        if (welcomeMessage) {
            welcomeMessage.textContent =
                `${greeting}, ${firstName} 👋`;
        }

        return user;

    } catch (error) {
        window.location.href = "/login/";
        return null;
    }
}

async function logout() {
    try {
        await fetch(
            "/api/logout",
            {
                method: "POST"
            }
        );

        window.location.href =
            "/login/";

    } catch (error) {
        showToast(
            "Unable to logout.",
            true
        );
    }
}

async function startApp() {
    const user =
        await checkAuthentication();

    if (!user) {
        return;
    }

    await refresh();
}

const logoutBtn =
    document.getElementById(
        "logoutBtn"
    );

if (logoutBtn) {
    logoutBtn.addEventListener(
        "click",
        logout
    );
}

startApp();

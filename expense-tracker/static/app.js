// ---------- Draw the category pie/doughnut chart (uses Chart.js) ----------
function drawCategoryChart(labels, values) {
    const canvas = document.getElementById("categoryChart");
    if (!canvas || typeof Chart === "undefined") return;

    new Chart(canvas, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: values,
                backgroundColor: [
                    "#4f46e5", "#06b6d4", "#f59e0b", "#ef4444",
                    "#10b981", "#8b5cf6", "#ec4899", "#6b7280"
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { position: "bottom" },
                tooltip: {
                    callbacks: {
                        label: function (ctx) {
                            return ctx.label + ": ₹" + ctx.parsed.toFixed(2);
                        }
                    }
                }
            }
        }
    });
}

document.addEventListener("DOMContentLoaded", function () {

    // ---------- Live search filter for the expense table ----------
    const search = document.getElementById("search");
    const table = document.getElementById("expense-table");
    if (search && table) {
        search.addEventListener("input", function () {
            const term = search.value.toLowerCase();
            table.querySelectorAll("tbody tr").forEach(function (row) {
                row.style.display = row.innerText.toLowerCase().includes(term) ? "" : "none";
            });
        });
    }

    // ---------- Ask for confirmation before deleting ----------
    document.querySelectorAll(".delete-form").forEach(function (form) {
        form.addEventListener("submit", function (e) {
            if (!confirm("Delete this expense?")) e.preventDefault();
        });
    });

    // ---------- Check that passwords match on the register page ----------
    const reg = document.getElementById("register-form");
    if (reg) {
        reg.addEventListener("submit", function (e) {
            const p = document.getElementById("password").value;
            const c = document.getElementById("confirm").value;
            if (p !== c) {
                e.preventDefault();
                alert("Passwords do not match.");
            }
        });
    }

    // ---------- Auto-hide flash messages after 4 seconds ----------
    document.querySelectorAll(".flash").forEach(function (msg) {
        setTimeout(function () { msg.style.display = "none"; }, 4000);
    });
});

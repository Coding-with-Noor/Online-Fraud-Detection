// ============================================================
// predict.js - Fraud Detection Form Logic
// Handles: quick-fill examples, form loading state, validation
// ============================================================

document.addEventListener("DOMContentLoaded", function () {

    // --- Quick-fill example buttons ---
    // Each button has data-* attributes with sample values
    const exampleBtns = document.querySelectorAll(".example-btn");

    exampleBtns.forEach(function (btn) {
        btn.addEventListener("click", function () {
            // Fill form fields with the example data
            document.querySelector("input[name='amount']").value         = btn.dataset.amount;
            document.querySelector("select[name='transaction_type']").value = btn.dataset.type;
            document.querySelector("input[name='sender_old_bal']").value  = btn.dataset.senderold;
            document.querySelector("input[name='sender_new_bal']").value  = btn.dataset.sendernew;
            document.querySelector("input[name='receiver_old_bal']").value = btn.dataset.recvold;
            document.querySelector("input[name='receiver_new_bal']").value  = btn.dataset.recvnew;

            // Scroll to form
            document.getElementById("fraudForm").scrollIntoView({ behavior: "smooth" });
        });
    });

    // --- Show loading state on form submit ---
    const form      = document.getElementById("fraudForm");
    const submitBtn = document.getElementById("submitBtn");

    if (form && submitBtn) {
        form.addEventListener("submit", function () {
            submitBtn.disabled    = true;
            submitBtn.innerHTML   = '<span class="spinner-border spinner-border-sm me-2"></span>Analyzing...';
        });
    }

});

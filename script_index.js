
const togglePassword = document.getElementById("togglePassword");
const password = document.getElementById("password");

togglePassword.addEventListener("click", function () {
    const type = password.type === "password" ? "text" : "password";
    password.type = type;
    

    const icon = togglePassword.querySelector("i");
    icon.classList = type === "password" ? "fas fa-eye-slash":"fas fa-eye"; 
});
     


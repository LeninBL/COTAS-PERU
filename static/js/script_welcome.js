document
  .getElementById("logout")
  .addEventListener("submit", async function (event) {
    event.preventDefault();

    try {
      await fetch("http://127.0.0.1:8000/logout", {
        method: "POST",
        credentials: "include",
      });

      window.location.href = "/access";
      if (window.location.href == "/access") {
        window.location.reload();
        console.error("sesión", error);
      }
      console.error(" cerrar sesión", error);
    } catch (error) {
      console.error("Error al cerrar sesión", error);
    }
  });

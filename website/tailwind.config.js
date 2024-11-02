/** @type {import('tailwindcss').Config} */
module.exports = {
    content: ["./templates/**/*.html", "./static/src/**/*.js"],
    theme: {
        extend: {},
    },
    daisyui: {
        themes: ["nord", "night"],
        darkTheme: "night",
    },
    plugins: [require("daisyui")],
};

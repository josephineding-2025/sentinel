/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Nunito", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      colors: {
        cream: {
          DEFAULT: "#F5F0E6",
          50: "#FBF9F4",
          100: "#F5F0E6",
          200: "#EDE5D3",
        },
        ink: {
          DEFAULT: "#3A2E27",
          light: "#6B5D53",
          faint: "#9C8F84",
        },
        sage: {
          DEFAULT: "#8CA888",
          50: "#F0F5EF",
          100: "#DCE8DA",
          200: "#B9D1B5",
          500: "#8CA888",
          600: "#6F8E6B",
          700: "#587056",
        },
        terracotta: {
          DEFAULT: "#E08A4F",
          50: "#FDF1E7",
          100: "#FADFC4",
          200: "#F2C08A",
          500: "#E08A4F",
          600: "#C96F36",
          700: "#A2571F",
        },
        coral: {
          DEFAULT: "#D96B5C",
          50: "#FBEAE7",
          100: "#F5CCC4",
          500: "#D96B5C",
          600: "#C1503F",
          700: "#993D2F",
        },
        lavender: {
          DEFAULT: "#A99BC7",
          50: "#F3F1F8",
          100: "#E3DDF0",
          500: "#A99BC7",
          600: "#8B79AE",
        },
      },
      borderRadius: {
        "2xl": "1.25rem",
        "3xl": "1.75rem",
      },
      boxShadow: {
        soft: "0 2px 12px -2px rgba(58, 46, 39, 0.08)",
        card: "0 4px 20px -4px rgba(58, 46, 39, 0.10)",
      },
    },
  },
  plugins: [],
};

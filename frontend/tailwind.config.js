/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: "class",
  theme: {
    extend: {
      "colors": {
              "surface-variant": "#2d3449",
              "tertiary-container": "#df7412",
              "surface-container-highest": "#2d3449",
              "surface-bright": "#31394d",
              "on-secondary": "#3c0091",
              "tertiary": "#ffb786",
              "on-secondary-fixed-variant": "#5516be",
              "on-error-container": "#ffdad6",
              "on-background": "#dae2fd",
              "outline-variant": "#424754",
              "on-primary-fixed-variant": "#004395",
              "surface-container": "#171f33",
              "on-surface": "#dae2fd",
              "on-tertiary": "#502400",
              "tertiary-fixed-dim": "#ffb786",
              "background": "#0b1326",
              "surface-container-low": "#131b2e",
              "on-primary": "#002e6a",
              "tertiary-fixed": "#ffdcc6",
              "on-primary-container": "#00285d",
              "secondary-fixed-dim": "#d0bcff",
              "surface-dim": "#0b1326",
              "surface-container-high": "#222a3d",
              "surface": "#0b1326",
              "error": "#ffb4ab",
              "inverse-on-surface": "#283044",
              "on-tertiary-container": "#461f00",
              "secondary-fixed": "#e9ddff",
              "on-secondary-container": "#c4abff",
              "secondary": "#d0bcff",
              "surface-container-lowest": "#060e20",
              "on-tertiary-fixed-variant": "#723600",
              "on-tertiary-fixed": "#311400",
              "inverse-primary": "#005ac2",
              "primary": "#adc6ff",
              "error-container": "#93000a",
              "primary-fixed": "#d8e2ff",
              "outline": "#8c909f",
              "on-surface-variant": "#c2c6d6",
              "on-error": "#690005",
              "primary-fixed-dim": "#adc6ff",
              "secondary-container": "#571bc1",
              "inverse-surface": "#dae2fd",
              "on-secondary-fixed": "#23005c",
              "surface-tint": "#adc6ff",
              "primary-container": "#4d8eff",
              "on-primary-fixed": "#001a42"
      },
      "borderRadius": {
              "DEFAULT": "0.125rem",
              "lg": "0.25rem",
              "xl": "0.5rem",
              "full": "0.75rem"
      },
      "spacing": {
              "unit": "4px",
              "gutter": "24px",
              "margin-mobile": "16px",
              "margin-desktop": "40px",
              "container-max": "1440px"
      },
      "fontFamily": {
              "headline-lg": [
                      "Inter"
              ],
              "label-caps": [
                      "Inter"
              ],
              "body-sm": [
                      "Inter"
              ],
              "body-md": [
                      "Inter"
              ],
              "headline-lg-mobile": [
                      "Inter"
              ],
              "headline-xl": [
                      "Inter"
              ],
              "data-display": [
                      "JetBrains Mono"
              ]
      },
      "fontSize": {
              "headline-lg": [
                      "32px",
                      {
                              "lineHeight": "1.2",
                              "letterSpacing": "-0.01em",
                              "fontWeight": "600"
                      }
              ],
              "label-caps": [
                      "12px",
                      {
                              "lineHeight": "1",
                              "letterSpacing": "0.05em",
                              "fontWeight": "700"
                      }
              ],
              "body-sm": [
                      "14px",
                      {
                              "lineHeight": "1.5",
                              "fontWeight": "400"
                      }
              ],
              "body-md": [
                      "16px",
                      {
                              "lineHeight": "1.6",
                              "fontWeight": "400"
                      }
              ],
              "headline-lg-mobile": [
                      "24px",
                      {
                              "lineHeight": "1.2",
                              "fontWeight": "600"
                      }
              ],
              "headline-xl": [
                      "48px",
                      {
                              "lineHeight": "1.1",
                              "letterSpacing": "-0.02em",
                              "fontWeight": "700"
                      }
              ],
              "data-display": [
                      "18px",
                      {
                              "lineHeight": "1.4",
                              "letterSpacing": "0.02em",
                              "fontWeight": "500"
                      }
              ]
      }
    },
  },
  plugins: [],
}

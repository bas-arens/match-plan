// /** @type {import('tailwindcss').Config} */
// module.exports = {
//   content: ['./index.html', './src/**/*.{vue,js,ts}'],
//   theme: {
//     extend: {
//       colors: {
//         brand: {
//           primary: '#2563EB',        // blue-600
//           primaryDark: '#1E40AF',    // blue-800
//           primaryLight: '#DBEAFE',   // blue-100
//           disabled: '#9CA3AF',       // gray-400
//           border: '#E5E7EB',         // gray-200

//           success: '#059669',        // emerald-600
//           danger: '#DC2626',         // red-600
//         }
//       }
//     }
//   },
//   plugins: [],
// }

// /** @type {import('tailwindcss').Config} */
// module.exports = {
//   content: ['./index.html', './src/**/*.{vue,js,ts}'],
//   theme: {
//     extend: {
//       colors: {
//         brand: {
//           // 💜 Purple brand
//           primary: '#7C3AED',         // violet-600
//           primaryDark: '#5B21B6',     // violet-700 (hover/active)
//           primaryDarker: '#4C1D95',   // violet-800 (selected)
//           primaryLight: '#EDE9FE',    // violet-100 (soft backgrounds)

//           // ⚪ Neutral system
//           disabled: '#9CA3AF',        // gray-400
//           border: '#E5E7EB',          // gray-200

//           // 🟢 / 🔴 Semantic
//           success: '#059669',         // emerald-600
//           danger: '#DC2626',          // red-600
//         }
//       }
//     }
//   },
//   plugins: [],
// }

/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./index.html', './src/**/*.{vue,js,ts}'],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#00DF82',
          primaryDark: '#00C974',
          primaryDarker: '#00B266',
          primaryLight: '#C6FFE7',

          dark: '#030F0F',
          darkSurface: '#0A1D1D',
          darkBorder: '#0E2020',

          light: '#F1F7F7',
          lightSurface: '#FFFFFF',
          lightBorder: '#D4E0E0',

          disabled: '#9CA3AF',
          border: '#E5E7EB',
          borderStrong: '#09090B', 

          success: '#00DF82',
          danger: '#DC2626',
        }
      }
    }
  },

  plugins: [
    function ({ addBase, theme }) {
      addBase({
        ':root': {
          '--brand-primary': theme('colors.brand.primary'),
          '--brand-primary-dark': theme('colors.brand.primaryDark'),
          '--brand-primary-darker': theme('colors.brand.primaryDarker'),
          '--brand-primary-light': theme('colors.brand.primaryLight'),

          '--brand-dark': theme('colors.brand.dark'),
          '--brand-dark-surface': theme('colors.brand.darkSurface'),
          '--brand-dark-border': theme('colors.brand.darkBorder'),

          '--brand-light': theme('colors.brand.light'),
          '--brand-light-surface': theme('colors.brand.lightSurface'),
          '--brand-light-border': theme('colors.brand.lightBorder'),

          '--brand-disabled': theme('colors.brand.disabled'),
          '--brand-border': theme('colors.brand.border'),
          '--brand-border-strong': theme('colors.brand.borderStrong'),

          '--brand-success': theme('colors.brand.success'),
          '--brand-danger': theme('colors.brand.danger'),
        }
      })
    }
  ],
}


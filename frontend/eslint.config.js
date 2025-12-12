import js from '@eslint/js'
import globals from 'globals'
import reactHooks from 'eslint-plugin-react-hooks'
import reactRefresh from 'eslint-plugin-react-refresh'
import tseslint from 'typescript-eslint'
import { defineConfig, globalIgnores } from 'eslint/config'

export default defineConfig([
    globalIgnores(['dist', '.yarn', 'src/components/ui']),
    {
        files: ['**/*.{ts,tsx}'],
        extends: [
            js.configs.recommended,
            tseslint.configs.recommended,
            reactHooks.configs.flat.recommended,
            reactRefresh.configs.vite,
        ],
        languageOptions: {
            ecmaVersion: 2020,
            globals: globals.browser,
        },
        rules: {
            "indent": ['warn', 4, { SwitchCase: 1 }],
            'import/no-unresolved': 'off',
            'no-process-env': 'off',
            'no-tabs': ['off'],
            // quotes: ['error', 'single'],
            'semi': ['error', 'always'],
            'no-unused-vars': 0,
            'no-case-declarations': 0,
            '@typescript-eslint/no-extraneous-class': 0,
            '@typescript-eslint/no-inferrable-types': 0,
            '@typescript-eslint/no-explicit-any': 0,
            '@typescript-eslint/no-duplicate-enum-values': 0,
            '@typescript-eslint/no-unused-vars': 0,
            '@typescript-eslint/no-unnecessary-type-constraint': 0,
            '@typescript-eslint/no-invalid-void-type': 0,
            "@typescript-eslint/no-non-null-assertion": 0,
            '@typescript-eslint/naming-convention': [
                'warn',
                {
                    selector: 'enumMember',
                    format: ['PascalCase'],
                    leadingUnderscore: 'allow',
                    trailingUnderscore: 'allow',
                },
                {
                    selector: 'variable',
                    format: ['camelCase', 'UPPER_CASE', 'snake_case', 'PascalCase'],
                },
                {
                    selector: 'class',
                    format: ['PascalCase'],
                },
                {
                    selector: 'parameter',
                    format: ['camelCase'],
                },
                {
                    selector: 'classMethod',
                    format: ['camelCase'],
                },
                {
                    selector: 'function',
                    format: ['camelCase', 'PascalCase'],
                },
                {
                    selector: 'interface',
                    format: ['PascalCase'],
                },
            ],
            "react-hooks/set-state-in-effect": 0
        },
    },
])

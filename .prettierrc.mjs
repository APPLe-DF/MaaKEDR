export default {
    plugins: [],
    tabWidth: 4,
    printWidth: 120,
    useTabs: false,
    bracketSameLine: true,
    bracketSpacing: false,
    endOfLine: "auto",
    overrides: [
        {
            files: [
                "*.json",
            ],
            options: {
                parser: "json",
                useTabs: false,
                bracketSameLine: false,
            },
        },
    ],
};

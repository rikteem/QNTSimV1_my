const JavaScriptObfuscator = require('webpack-obfuscator');
module.exports = (config, options) => {
    if (config.mode === 'production') {
        config.plugins.push(new JavaScriptObfuscator({
            rotateStringArray: true,
            simplify: true,
            sourceMap: false,
            sourceMapMode: 'separate',
            target: 'browser',
        }, ['exclude_bundle.js']));
    }
}
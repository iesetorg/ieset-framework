// Stub for any `bare-*` package that webpack resolves from a parent
// directory's node_modules and tries to ship into the browser bundle.
// These packages expose Node-native bindings that crash at runtime in
// the browser. Returning an empty object lets the import statement
// succeed without invoking anything.
module.exports = {};
module.exports.default = {};

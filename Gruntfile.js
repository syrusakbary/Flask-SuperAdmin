// Grunt config file to help with static JS assets - run the requirejs optimizer, compilation, etc.
// https://github.com/gruntjs/grunt/
module.exports = function(grunt) {

    grunt.loadNpmTasks('grunt-contrib');

    grunt.initConfig({

        jshint: {
            all: [
                'flask_superadmin/static/js/filters.js',
                'flask_superadmin/static/js/form.js'
            ],
            options: {
                scripturl: true,
                expr: true,
                multistr: true
            }
        },

    });

    grunt.registerTask('lint', 'jshint');

};

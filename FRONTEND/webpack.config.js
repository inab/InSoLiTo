const path = require('path');
const webpack = require('webpack');
const HtmlWebpackPlugin = require('html-webpack-plugin');
const ESLintPlugin = require('eslint-webpack-plugin');

const PATHS = {
	app: path.resolve(__dirname,'app'),
	dist: path.resolve(__dirname,'..','REST','static')
};

function escapeRegExpString(str) { return str.replace(/[\-\[\]\/\{\}\(\)\*\+\?\.\\\^\$\|]/g, "\\$&"); }
function pathToRegExp(p) { return new RegExp("^" + escapeRegExpString(p)); }

module.exports = {
	mode: 'development',
	entry: {
		path: path.join(PATHS.app, 'main.js'),
	},
	output: {
		filename: 'bundle.js',
		path: PATHS.dist,
	},
	plugins:[
		new ESLintPlugin({
			files: PATHS.app
		}),
		new webpack.ProvidePlugin({
			$: 'jquery',
			$: 'jquery-ui',
			vis: 'vis-network'
		}),
		new HtmlWebpackPlugin({
			title: 'InSoLiTo web site',
			template: 'app/index.html',
			filename: path.join(PATHS.dist,'index.html')
		}),
	],
	module: {
		rules: [
			{
				test: /\.js$/,
				exclude: /(node_modules|bower_components)/,
				use: {
					loader: 'babel-loader',
					options: {
						presets: [
							'@babel/preset-env',
//    							['@babel/preset-stage-2',{'useBuiltIns': true, 'decoratorsLegacy': true}],
						],
						plugins: [
							["module:@babel/plugin-proposal-decorators", { "legacy": true }],
							"module:@babel/plugin-proposal-function-sent",
							"module:@babel/plugin-proposal-export-namespace-from",
							"module:@babel/plugin-proposal-numeric-separator",
							"module:@babel/plugin-proposal-throw-expressions",
						]
					}
				}
			},
			{
				test: /\.js$/,
				enforce: "pre",
				use: ["source-map-loader"],
				
			},			
			{
				test: /\.css$/,
				use: ['style-loader','css-loader']
			},
			{
				test: /\.(png|svg)$/,
				loader: "file-loader",
				options: {
					outputPath: 'images'
				},


			}
		]
	}
};

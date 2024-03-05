const path = require('path');
const HtmlWebpackPlugin = require('html-webpack-plugin');

const PATHS = {
	src: path.resolve(__dirname,'src'),
	dist: path.resolve(__dirname,'..','REST','static')
};


module.exports = {
  entry: {
    path: path.join(PATHS.src, 'main.js'),
	},
  output: {
    filename: 'bundle.js',
    path: PATHS.dist,
    clean: true,
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: 'InSoLiTo graph',
      template: path.join(PATHS.src, 'index.html'),
      filename: path.join(PATHS.dist,'index.html')
 
    }),
  ],
  module: {
    rules: [
      {
        test: /\.css$/i,
        use: ['style-loader', 'css-loader'],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: 'asset/resource',
      },
    ],
  },
};

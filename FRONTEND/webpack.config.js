const path = require("path");
const autoprefixer = require("autoprefixer");
const HtmlWebpackPlugin = require("html-webpack-plugin");

const PATHS = {
  src: path.resolve(__dirname, "src"),
  dist: path.resolve(__dirname, "..", "REST", "static"),
};

module.exports = {
  entry: {
    path: path.join(PATHS.src, "main.js"),
  },
  output: {
    filename: "bundle.js",
    path: PATHS.dist,
    clean: true,
  },
  devtool: "eval-source-map",
  devServer: {
    static: {
      directory: path.join(__dirname, "src"),
    },
    compress: true,
    port: 9000,
    client: {
      logging: "error",
      overlay: false,
    },
  },
  plugins: [
    new HtmlWebpackPlugin({
      title: "InSoLiTo graph",
      template: path.join(PATHS.src, "index.html"),
      filename: path.join(PATHS.dist, "index.html"),
    }),
  ],
  module: {
    rules: [
      {
        test: /\.scss$/i, // Procesa archivos .scss
        use: [
          "style-loader", // Añade estilos al DOM
          "css-loader", // Interpreta @import y url()
          {
            loader: "postcss-loader", // PostCSS para autoprefixer
            options: {
              postcssOptions: {
                plugins: [autoprefixer],
              },
            },
          },
          "sass-loader", // Compila SCSS a CSS
        ],
      }
      ,{
        test: /\.css$/i,
        use: [
          "style-loader",
          "css-loader",
          {
            loader: 'postcss-loader',
            options: {
              postcssOptions: {
                plugins: [
                  autoprefixer
                ]
              }
            }
          }
        ],
      },
      {
        test: /\.(png|svg|jpg|jpeg|gif)$/i,
        type: "asset/resource",
      },
    ],
  },
};

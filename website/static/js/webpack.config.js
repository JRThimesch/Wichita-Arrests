module.exports = {
    mode: 'development',
    entry: './Maps.js',
    output: {
      filename: 'bundle.js',
      publicPath: 'dist'
    },
    module: {
      rules: [
        {
          test: /\.js$/,
          exclude: /node_modules/,
          use: {
            loader: 'babel-loader',
          }
        },
        {
            test:/\.css$/,
            use:['style-loader', 'css-loader']
        }
      ]
    }
};
$(function() {
  // myFormがsubmitされる時
  $('.myForm').submit(function() {
    // text1が入力されていなければ
    if($('.text1').val() == "") {
      // alertを出して
      alert("何か入力してください。");
      // submitを止める
      return false;
    }
    if($('.text2').val() == "") {
      // alertを出して
      alert("何か入力してください。");
      // submitを止める
      return false;
    }
  });
});
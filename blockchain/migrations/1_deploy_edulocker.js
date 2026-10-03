const EduLocker = artifacts.require("EduLocker");

module.exports = function (deployer) {
  deployer.deploy(EduLocker);
};